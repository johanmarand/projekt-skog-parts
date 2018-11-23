import numpy as np
import os
import pandas as pd
import random

from attr import attrs, attrib
from keras.layers import Dense
from keras.models import Sequential
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib

from . import cfg_data_grid
from . import cfg_models
from .data_grid import DataGrid
from .db_manager import DbManager
from . import cfg
from . import locale
from . import utils


@attrs
class ModelBuilder(object):
    name = attrib()  # Name of model to work with
    version = attrib()  # Version (1, 2, 3 etc, only non-decimal)

    # Set by class
    data_grid = attrib(init=False)
    model = attrib(init=False)

    @classmethod
    def clean_cells(cls, cells, model_name):
        # Drop columns not relevant for this model
        df = cells.drop(cfg_models.MODELS[model_name]['exclude_cols'], axis=1)

        # Set -1 values to np.nan
        df = df.replace(-1, np.nan)

        # Drop all rows missing data
        df = df.dropna()  # drop all rows that have any NaN values

        return df

    def file_name(self, suffix='', extension=None):
        file = 'model_{name}_{version}_{suffix}'.format(name=self.name, version=str(self.version), suffix=suffix)

        if extension:
            file = file + extension

        return file

    def collect_data(self, kind='high', sample_size=10):
        # Load SQL file for training data
        sql_file = self.file_name(suffix=kind)
        sql = utils.sql_template(sql_file)
        gdf = DbManager.get_gdf(sql)

        # For every polygon
        for i, row in gdf.iterrows():
            # Cut up the polygon into reasonable size (300 m on the long side)
            polygons = utils.katana(row.geom, 300)

            # Get a random sample of polygons
            if len(polygons) > sample_size:
                samples = random.sample(polygons, sample_size)
            else:
                samples = polygons

            # For each smaller polygon
            for p in samples:
                # Get the data grid, so that we know which cells are being collected as training data
                dg = DataGrid.grid_from_polygon(p)

                # Get the data grid ids as a list
                cell_ids = dg.grid['id'].tolist()

                # Store the model info and cells (training data) in db
                for cell_id in cell_ids:
                    sql = ("INSERT INTO ps_model_training (model_id, model_version, cell_id, biodiversity) "
                           "SELECT '{model_id}', {model_version}, {cell_id}, '{biodiversity}' "
                           "WHERE NOT EXISTS ("
                           "SELECT 1 FROM ps_model_training "
                           "WHERE model_id = '{model_id}' AND model_version={model_version} AND cell_id = {cell_id}"
                           ")").format(model_id=self.name,
                                       model_version=self.version,
                                       cell_id=cell_id,
                                       biodiversity=kind)

                    DbManager.exec_sql(sql)

                # Create locale, set partition_key to "model" to differentiate (who cares? won't be saved anywhere)
                locale_row_key = str(row.id)
                loc = locale.Locale(polygon=p, partition_key='model', row_key=locale_row_key)

                # Load data for locale, but skip FOI, we only need the data grid cells
                loc.load(foi=False)

    def _prepare_for_training(self):
        """
        Loads the model data cells from db, and prepares for training
        """
        sql = ("SELECT v.*, "
               "CASE WHEN m.biodiversity='high' THEN 1 WHEN m.biodiversity='low' THEN 0 END AS biodiversity "
               "FROM ps_data_grid_val v, ps_model_training m "
               "WHERE v.id = m.cell_id "
               "AND m.model_id = '{model_id}' "
               "AND m.model_version = {model_version} ").format(model_id=self.name, model_version=self.version)

        df = pd.read_sql(sql, DbManager.engine(), index_col='id')
        self.data_grid = ModelBuilder.clean_cells(df, self.name)

    def train_sklearn(self):
        # Data preparation
        self._prepare_for_training()
        df = self.data_grid

        # Create two new dataframes, one with the training rows, one with the test rows
        df['is_train'] = np.random.uniform(0, 1, len(df)) <= .75
        train, test = df[df['is_train'] == True], df[df['is_train'] == False]

        # Create a list of the feature column's names (excluding the ones the model wants excluded)
        features = list(set([key for key, val in cfg_data_grid.GRID_FEATURES.items()]) - \
                        set(cfg_models.MODELS[self.name]['exclude_cols']))

        # Set the "truth"
        y = train['biodiversity']

        # Create a random forest classifier. By convention, clf means 'classifier'
        clf = RandomForestClassifier(n_jobs=2)

        # Train the classifier to take the training features and learn how they relate to the training y
        clf.fit(train[features], y)

        # Apply the classifier we trained to the test data (which, remember, it has never seen before)
        clf.predict(test[features])

        # Create actual english names for the predicted biodiversity probability
        target_names = np.array(['low', 'high'])
        preds = target_names[clf.predict(test[features])]

        # Create confusion matrix (debug to see this)
        confusion_matrix = pd.crosstab(test['biodiversity'], preds, rownames=['Actual'], colnames=['Predicted'])

        # Save file
        file = self.file_name(suffix='sklearn', extension='.pkl')
        joblib.dump(clf, os.path.join(cfg.PATH_MODELS, file))

    def train_keras(self):
        # Data preparation
        self._clean_and_prepare()

        # fix random seed for reproducibility
        seed = 7
        np.random.seed(seed)

        len_x = len(list(self.data_grid)) - 1

        # split into input (X) and output (Y) variables
        X = self.data_grid.iloc[:, 0:len_x]
        Y = self.data_grid.iloc[:, len_x]

        # create model
        model = Sequential()
        model.add(Dense(12, input_dim=len_x, kernel_initializer='uniform', activation='relu'))
        model.add(Dense(len_x, kernel_initializer='uniform', activation='relu'))
        model.add(Dense(1, kernel_initializer='uniform', activation='sigmoid'))

        # Compile model
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

        # Fit the model
        model.fit(X, Y, epochs=150, batch_size=10, verbose=0)

        # evaluate the model
        scores = model.evaluate(X, Y, verbose=0)
        print("%s: %.2f%%" % (model.metrics_names[1], scores[1] * 100))

        # serialize model to JSON
        model_json = model.to_json()
        file = self.file_name(suffix='keras', extension='json')
        with open(file, "w") as json_file:
            json_file.write(model_json)

        # serialize weights to HDF5
        model.save_weights("model.h5")
        print("Saved model to disk")

        self.model = model
        self.data = X

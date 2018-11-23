# Get data for a cell even if the row already is in ps_grid_data_val
# If set to True, the UPDATE_ONLY_DYNAMIC_DATA will determine if all data, or only dynamic data will be updated
# If set to False, no data will be updated. This is useful i.e. to speed up getting data for model building
# Default: True
UPDATE_IF_EXISTS = True

# Get only "dynamic" data, meaning data that changes quite often
# Controlled by the 'dynamic' attribute
# Default: True
UPDATE_ONLY_DYNAMIC_DATA = True

GRID_FEATURES = {
    'artobservation_signalart_dist': {'type': 'dist', 'table_name': 'ps_mview_signalarter', 'update': 'dynamic'},
    'artobservation_rodlista_dist': {'type': 'dist', 'table_name': 'ps_mview_signalarter', 'update': 'dynamic',
                                     'where': 'rodlista IS NOT NULL'},
    'biotopskydd_dist': {'type': 'dist', 'table_name': 'ps_mview_biotopskydd', 'update': 'dynamic'},
    'naturreservat_dist': {'type': 'dist', 'table_name': 'naturreservat', 'update': 'static'},
    'naturvarde_dist': {'type': 'dist', 'table_name': 'ps_mview_naturvarden', 'update': 'dynamic'},
    'naturvardsavtal_dist': {'type': 'dist', 'table_name': 'ps_mview_naturvardsavtal', 'update': 'dynamic'},
    'nyckelbiotop_dist': {'type': 'dist', 'table_name': 'ps_mview_nyckelbiotoper', 'update': 'dynamic'},
    # TODO: Nyckelbiotoper bolag
    # 'nyckelbiotop_bolag_dist': {'type': 'dist', 'table_name': 'ps_mview_nyckelbiotoper_bolag', 'update': 'dynamic'},
    'vag_dist': {'type': 'dist', 'table_name': 'vagkartan_vl', 'update': 'static'},
    'vandringsled_dist': {'type': 'dist', 'table_name': 'oversiktskartan_bo',
                          'where': "kkod IN (5561, 5561, 5571, 5571)", 'update': 'static'},
    'vattenyta_dist': {'type': 'dist', 'table_name': 'vattenytor', 'update': 'static'},
    'vattendrag_dist': {'type': 'dist', 'table_name': 'vattendragslinjer', 'update': 'static'},
    'tatort_dist': {'type': 'dist', 'table_name': 'tatorter', 'update': 'static'},
    'smaort_dist': {'type': 'dist', 'table_name': 'smaorter', 'update': 'static'},
    'kalla_dist': {'type': 'dist', 'table_name': 'kallor', 'update': 'static'},
    'sumpskog_dist': {'type': 'dist', 'table_name': 'sumpskogar', 'update': 'static'},
    'utford_avverkning_dist': {'type': 'dist', 'table_name': 'ps_mview_utford_avverkning', 'update': 'dynamic'},

    'myrskyddsplan': {'type': 'bool', 'table_name': 'myrskyddsplan', 'update': 'static'},
    'kontinuitetsskog_boreal': {'type': 'bool', 'table_name': 'kontinuitetsskog_boreal', 'update': 'static'},
    'riksintresse_friluftsliv': {'type': 'bool', 'table_name': 'riksintresse_friluftsliv', 'update': 'static'},
    'riksintresse_naturvard': {'type': 'bool', 'table_name': 'riksintresse_naturvard', 'update': 'static'},
    'riksintresse_vattendrag': {'type': 'bool', 'table_name': 'riksintresse_vattendrag', 'update': 'static'},

    'hojd': {'type': 'raster', 'table_name': 'ris_height', 'update': 'static'},
    'alder': {'type': 'raster', 'table_name': 'ris_age_auto', 'update': 'static'},
    'granvol': {'type': 'raster', 'table_name': 'ris_pinevol', 'update': 'static'},
    'tallvol': {'type': 'raster', 'table_name': 'ris_sprucevol', 'update': 'static'},
    'lovvol': {'type': 'raster', 'table_name': 'ris_deciduousvol', 'update': 'static'},
    'bokvol': {'type': 'raster', 'table_name': 'ris_beechvol_auto', 'update': 'static'},
    'bjorkvol': {'type': 'raster', 'table_name': 'ris_birchvol', 'update': 'static'},
    'medeldiameter': {'type': 'raster', 'table_name': 'medeldiameter', 'update': 'static'},
    'medelhojd': {'type': 'raster', 'table_name': 'medelhojd', 'update': 'static'},
    'grundyta': {'type': 'raster', 'table_name': 'grundyta', 'update': 'static'},
    'arsnederbord': {'type': 'raster', 'table_name': 'arsnederbord', 'update': 'static'},
    'arsmedeltemperatur': {'type': 'raster', 'table_name': 'arsmedeltemperatur', 'update': 'static'},
    'markhojd': {'type': 'raster', 'table_name': 'nh_riks', 'update': 'static'},
    'lutning': {'type': 'raster', 'table_name': 'lutning', 'update': 'static'},

    'jordart': {'type': 'value_at', 'table_name': 'jordarter', 'value_col': 'jg2', 'hashed_value_col': False,
                'update': 'static'},
    'sumpskog': {'type': 'value_at', 'table_name': 'sumpskogar', 'value_col': 'hydrtext', 'hashed_value_col': True,
                 'update': 'static'},

    'berggrund': {
        'type': 'custom',
        'sql': ("WITH custom_val AS ("
                "SELECT COALESCE(l.brg, y.brg) as val, p.id as point_id "
                "FROM ps_data_grid p "
                "LEFT JOIN berggrundslinjer l ON (ST_DWithin(p.geom, l.geom, 112.5)) "
                "LEFT JOIN berggrundsytor y ON (ST_DWithin(p.geom, y.geom, 12.5)) "
                "WHERE p.id IN ({id_list})) "
                "UPDATE ps_data_grid_val SET berggrund = c.val "
                "FROM custom_val c "
                "WHERE id = c.point_id"),
        'update': 'static'},
}

import cdsapi

c = cdsapi.Client()

c.retrieve(
    'efas-forecast',
    {
        'format': 'netcdf4.zip',
        'system_version': 'operational',
        'originating_centre': 'ecmwf',
        'product_type': 'high_resolution_forecast',
        'variable': 'river_discharge_in_the_last_6_hours',
        'model_levels': 'surface_level',
        'year': '2024',
        'month': '03',
        'day': [
            '16', '17', '18',
            '19', '20', '21',
            '22', '23', '24',
            '25',
        ],
        'time': '00:00',
        'leadtime_hour': [
            '6', '12', '18',
            '24',
        ],
        'area': [
            48, 6, 35,
            25,
        ],
    },
    'download_202403qb_forecast.netcdf4.zip')

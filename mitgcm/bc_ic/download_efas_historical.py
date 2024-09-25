import cdsapi

c = cdsapi.Client()

c.retrieve(
    'efas-historical',
    {
        'format': 'netcdf4.zip',
        'system_version': 'version_5_0',
        'variable': 'river_discharge_in_the_last_6_hours',
        'model_levels': 'surface_level',
        'hyear': '2023',
        'hmonth': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
        ],
        'hday': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            '13', '14', '15',
            '16', '17', '18',
            '19', '20', '21',
            '22', '23', '24',
            '25', '26', '27',
            '28', '29', '30',
            '31',
        ],
        'time': [
            '00:00', '06:00', '12:00',
            '18:00',
        ],
        'area': [
            48, 6, 35,
            25,
        ],
    },
    'download_2023_historical.netcdf4.zip')

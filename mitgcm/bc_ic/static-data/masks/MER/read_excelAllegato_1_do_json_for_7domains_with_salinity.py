# read the Allegato1 excel file and select the domain from 1 to 7 and 
# build the json files with the coordinate of the pointsource for E.Coli tracers
import numpy as np
import pandas as pd
import json
import os
import copernicusmarine as cm

# Allegato 1 of sewage discharge locations 
excel_file = 'Allegato_1_Capitolato_Tecnico_B32_B35_modificato.xlsx'
# select the n. of domain from 1 to 7 and name the json file
WHICH_DOMAIN=1
#output_file = 'PointSource_nordadri.json'
domains=['NAD','SAD','ION','SIC','TYR','LIG','SAR']

# subset and read CMS reanalysis for salinity
x0, x1 = 6.5000, 21.0000 #12.22265625, 16.07421875
y0, y1 = 35.0000, 45.80859375 #43.47265625, 45.80859375
z0, z1 = 1.0182366371154785, 5754.

t0 = '2012-01-01T00:00:00'
t1 = '2021-12-31T00:00:00'

dataset = 'med-cmcc-sal-rean-d'
var = 'so'

sal = cm.open_dataset(
    username = 'fgiordanoCMS',
    password = 'giordy98÷CMEMS',
    dataset_id = dataset,
    #dataset_version = version,
    variables = [var],
    minimum_longitude = x0,
    maximum_longitude = x1,
    minimum_latitude = y0,
    maximum_latitude = y1,
    start_datetime = t0,
    end_datetime = t1,
    minimum_depth = z0,
    maximum_depth = z1,
)

Lon, Lat = np.meshgrid(sal.longitude.values, sal.latitude.values)
Lon = Lon * np.where(sal.so[0,0,:,:] == sal.so[0,0,:,:], 1, np.nan)
Lat = Lat * np.where(sal.so[0,0,:,:] == sal.so[0,0,:,:], 1, np.nan)

#import matplotlib.pyplot as plt
#import cmocean as cmo
#sal.so[0,0,:,:].plot.imshow(); plt.show()

dataset = 'cmems_mod_med_phy_my_4.2km_static'
var = 'deptho_lev'

bathyCMS = cm.open_dataset(
    username = 'fgiordanoCMS',
    password = 'giordy98÷CMEMS',
    dataset_id = dataset,
    #dataset_version = version,
    variables = [var],
    minimum_longitude = x0,
    maximum_longitude = x1,
    minimum_latitude = y0,
    maximum_latitude = y1,
    minimum_depth = z0,
    maximum_depth = z1,
)['deptho_lev']

print('Loaded datasets!')

# Extract the Excel file name without extension
file_name = os.path.splitext(os.path.basename(excel_file))[0]

# Read the Excel file into a DataFrame
df = pd.read_excel(excel_file)

for id, namedomain in enumerate(domains):

  # Filter rows where the value in column 'Dominio' is id+1 (valid number from 1 to 7)
  filtered_df = df[df['Dominio'] == id+1]

  # Select only the interesting columns 
  selected_columns = filtered_df[['Codice_Scarico', 'Lat', 'Long','Carico_Ingresso_AE', 'Nome_scarico','Regione']]

  depths = []
  Savg = []
  Sstd = []
  dilut_fac = 1.
  for scol in range(selected_columns.shape[0]):
      lat_df = selected_columns.Lat.to_numpy()[scol]
      lon_df = selected_columns.Long.to_numpy()[scol]
      #j = np.nanargmin(np.abs(lat_df - sal.latitude.values)) ##
      #i = np.nanargmin(np.abs(lon_df - sal.longitude.values)) ##
      idx = np.nanargmin((Lon-lon_df)**2 + (Lat-lat_df)**2)
      #if np.shape(lon_df) == ():
      #	j, i = idx//1, idx%1
      #else:
      #	j, i = idx//len(lon_df), idx%len(lon_df)
      j, i = idx//len(sal.longitude.values), idx%len(sal.longitude.values)
      k = bathyCMS[j, i].values
      kn = int(np.where(np.isnan(k), 0, k - 1))
      depths.append(sal.depth[kn].values * k / k)
      Savg.append(np.mean(sal.so[:, kn, j, i].values * k / k))
      Sstd.append(np.std(sal.so[:, kn, j, i].values * k / k))

  selected_columns.insert(5, "CMS_depth", depths, True)
  selected_columns.insert(6, "CMS_avgS", Savg, True)
  selected_columns.insert(7, "CMS_stdS", Sstd, True)
  selected_columns.insert(8, "Dilution_factor", dilut_fac, True)

  # Convert the selected rows to a list of dictionaries
  filtered_rows = selected_columns.to_dict(orient='records')

  # Create the final JSON structure
  output_data = {
      "file_name_origin": file_name,
      "domain_number": id+1,
      "domain_name": domains[id],
      "n_points": len(filtered_rows),
      "discharge_points": filtered_rows
  }
  # build the output file name
  output_file = 'PointSource_wSalt_' + domains[id] + '.json'
  # Write the final JSON structure to a JSON file
  with open(output_file, 'w') as json_file:
      json.dump(output_data, json_file, indent=4)
    
  print(f"JSON file created: {output_file}")


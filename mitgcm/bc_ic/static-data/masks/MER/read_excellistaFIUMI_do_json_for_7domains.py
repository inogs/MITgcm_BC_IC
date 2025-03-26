# read the listaFIUMI_MER excel file and select the domain from 1 to 7 and 
# build the json files with the coordinate of the riversource for E.Coli tracers
import pandas as pd
import json
import os
import sys

# Allegato 1 of sewage discharge locations 
excel_file = 'listaFIUMI_MER.xlsx'
base_path = sys.argv[1]
data_path = sys.argv[2]
# select the n. of domain from 1 to 7 and name the json file

domains=['NAD','SAD','ION','SIC','TYR','LIG','SAR', 'GoT', 'GSN']


# Extract the Excel file name without extension
file_name = os.path.splitext(os.path.basename(excel_file))[0]

# Read the Excel file into a DataFrame
df = pd.read_excel(data_path+excel_file)

for id, namedomain in enumerate(domains):

  # Filter rows where the value in column 'Dominio' is id+1 (valid number from 1 to 7)
  if id < 7:
      filtered_df = df[df['Dominio'] == id+1]
  else:
      filtered_df = df[df['Sotto-Dominio'] == 8]  ### hardcoded horribly !!!

  # Select only the interesting columns 
  selected_columns = filtered_df[['rivername', 'lat_mouth', 'lon_mouth','MEAN_2011_2023', 'catchment','Region']]

  # Convert the selected rows to a list of dictionaries
  filtered_rows = selected_columns.to_dict(orient='records')

  # Create the final JSON structure
  output_data = {
      "file_name_origin": file_name,
      "domain_number": id+1,
      "domain_name": domains[id],
      "n_points": len(filtered_rows),
      "river_points": filtered_rows
  }
  output_file = base_path + domains[id] + '/RiverSource_' + domains[id] + '.json'
  # build the output file name
  # Write the final JSON structure to a JSON file
  with open(output_file, 'w') as json_file:
      json.dump(output_data, json_file, indent=4)
    
  print(f"JSON file created: {output_file}")


How to generate the csv files with tha data of the river discharges
-----------------------------------------------------------------------

This README file outlines the procedure used to generate CSV files containing
river discharge data from the corresponding XLSX files.

This procedure has been implemented to avoid dependency on proprietary XLSX
files within the operational scripts. However, it introduces a duplicated
source of information that must be kept synchronized: the XLSX file and the
CSV file. While the XLSX files are useful for visualizing the data
conveniently, the files that are essential for the software are the CSV files.

If you modify any of the XLSX files, you must regenerate the corresponding CSV
file. There are two procedures to accomplish this task, both of which produce
the same CSV file (with minor rounding differences)


1. By using the Python interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write the following line::

    rivers.save_river_csv(RIVERS, bgc_vars, output_path=PATH_OF_THE_CSV_FILE)

at the end of the `read_XLS.py' file. PATH_OF_THE_CSV_FILE must be a string
(or a Path object from the pathlib library) with the path of the file that
you want to write.

Set a env variable named "RIVERDATA" to the path of the XLSX file that
contains the input data.

Run the script `reas_XLS.py" it's then enough to generate the CSV file.



2. By exporting the data directly from Excel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open the XLSX file you want to export directly using Excel. Copy the cells
that you want to export to another sheet. Usually, this means copying the
first row with the names of the variables, skipping the second one with
the units of measurement and then copy all the other lines.
In the new sheet, save it as a CSV file. This generates a CSV file with
all the data needed by the software.

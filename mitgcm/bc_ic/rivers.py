from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Union
import warnings

import numpy as np
import pandas as pd
import csv

from bitsea.commons import genUserDateList as DL


@dataclass(frozen=True)
class BGCVar:
    id: int
    name: str
    unit: Union[str, None] = None


class River:
    def __init__(self, data_row, meteo_dir):
        """
        data_row is a row of an Excel file ordered in the same way of this
        constructor
        """
        data_row = tuple(data_row)
        self.ind: int = int(data_row[0])
        self.name: str = str(data_row[1])
        self.type_of_ave: str = str(data_row[2])
        self.iLon: int = int(data_row[3])
        self.iLat: int = int(data_row[4])
        self.side: str = str(data_row[5])
        self.nVcells: int = int(data_row[6])
        self.nHcells: int = int(data_row[7])
        self._original_Q_mean: float = float(data_row[8])
        self.Q_mean: float = float(data_row[8])
        self.applied_ratio: bool = False
        self.sali: float = 15.0

        n_var = len(data_row) - 9

        self.Conc = np.zeros((n_var,), np.float32)
        for ivar in range(n_var):
            self.Conc[ivar] = data_row[9 + ivar]

        self.meteo_dir = Path(meteo_dir).absolute()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        equal = self.name == other.name and self.ind == other.ind
        equal &= self.iLat == other.iLat and self.iLon == other.iLon
        equal &= self.type_of_ave == other.type_of_ave
        equal &= self.side == other.side

        if not equal:
            return False

        equal = self.nVcells == other.nVcells and self.nHcells == other.nHcells
        equal &= self.applied_ratio == other.applied_ratio

        if not equal:
            return False

        equal = np.allclose(self.Q_mean, other.Q_mean)
        equal &= np.allclose(self.sali, other.sali)
        equal &= np.allclose(self.Conc, other.Conc)

        equal &= self.meteo_dir == other.meteo_dir

        return equal

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        if self.ind < other.ind:
            return True

        if self.ind == other.ind:
            return self.name < other.name

        return False

    def __le__(self, other):
        if self == other:
            return True
        return self < other

    def get_ratio(self):
        """
        Return ratio between actual mean discharge and the
        climatological one read from xls
        """
        ratio = np.nan
        filename = self.meteo_dir / (self.name + ".txt")
        if filename.exists():
            _, actual_Q = self.read_discharge_file(filename)
            ratio = actual_Q.mean() / self.Q_mean
        return ratio

    def apply_ratio(self, ratio):
        if not self.applied_ratio:
            self.Q_mean = self.Q_mean * ratio
            self.applied_ratio = True


    def getTimeDischarge(self, timelist):
        """
        Behaviour climatologic if river is classified as 'yearly clim.'
        or if is not possible to find the file having the same name of the
        river + '.txt'
        """

        if self.type_of_ave == 'yearly clim.':
            return self.getClimTimeDischarge(timelist)
        else:
            filename = self.meteo_dir / (self.name + ".txt")
            if filename.exists():
                print(" ****************  Found  {}".format(filename))
                TLfound, Q = self.read_discharge_file(filename)
                return self.Time_interp(Q, TLfound, timelist)
            else:
                warnings.warn(
                    "{} file not found. Climatological data will be used"
                    "instead.".format(filename)
                )
                return self.getClimTimeDischarge(timelist)

    @staticmethod
    def read_discharge_file(filename):
        """ Reads file in the format yyyymmdd-hh:MM:ss Q """
        DT = [('date', 'U17'), ('Q', np.float32)]
        A = np.loadtxt(filename, dtype=DT)
        return A['date'], A['Q']

    @staticmethod
    def Time_interp(Q, timelist_in, timelist_out):
        n_frames_in = len(timelist_in)
        n_frames_out = len(timelist_out)
        Tin = np.zeros((n_frames_in,), np.float32)
        Tout = np.zeros((n_frames_out,), np.float32)

        for i in range(n_frames_in):  Tin[i] = float(
            DL.readTimeString(timelist_in[i]).strftime("%s"))
        for i in range(n_frames_out): Tout[i] = float(
            DL.readTimeString(timelist_out[i]).strftime("%s"))
        return np.interp(Tout, Tin, Q)

    def getClimTimeDischarge(self, timelist):
        """
        Discharges are calculated by a formula
        a sinusoid  - having T=365/2 days, min=0.25, max=1.75 at julian day 120 -
        modulating mean annual discharge provided in xls file.
        """
        n_frames = len(timelist)
        Q = np.zeros((n_frames,), np.float32)
        for it, timestring in enumerate(timelist):
            D = DL.readTimeString(timestring)
            julian = int(D.strftime("%j"))
            modulation_factor = 1.0 + 0.75 * np.cos(
                2 * (2 * np.pi * (julian - 120.) / 365)
            )
            Q[it] = self.Q_mean * modulation_factor
        return Q

    def getTimeTemperature(self, timelist):
        """
        Temperatures are calculated by a formula, a sinusoid having T=365 days,
        min = 5 deg, max=15 deg at julian day 212.
        """
        nFrames = len(timelist)
        T = np.zeros((nFrames,), np.float32)
        for it, timestring in enumerate(timelist):
            D = DL.readTimeString(timestring)
            julian = int(D.strftime("%j"))
            T[it] = 10.0 + 5 * np.cos((2 * np.pi * (julian - 212.) / 365))
        return T


def get_RiverBFM_Data(lato, varname, river_list, var_list):
    """
    Concentration of Biogeochemical variables is intended not to change in time
    Returns :
    integer array Lon_Ind[nRivers] of Longitude Indexes
    integer array Lat_Ind[nRivers] of Latitude  Indexes
    float array  OUT[nRiver] for the required variable

    lato can be 'E','S','W' or 'N'
    varname is a BFM variable such as 'N1p'
    """

    nLato = 0
    for R in river_list:
        if R.side == lato:
            nLato += 1

    Lon_Ind = np.zeros(nLato, np.int32)
    Lat_Ind = np.zeros(nLato, np.int32)
    conc = np.zeros(nLato, np.float32)

    counter = 0
    for R in river_list:
        if R.side == lato:
            Lon_Ind[counter] = R.iLon - 1
            Lat_Ind[counter] = R.iLat - 1

            for i in range(len(var_list)):
                if var_list[i].name == varname:
                    break
            else:
                raise ValueError('Invalid variable: "{}"'.format(varname))
            conc[counter] = R.Conc[i]
            counter = counter + 1
    return Lon_Ind, Lat_Ind, conc


def get_RiverPHYS_Data(lato, varname, timelist, Mask, river_list):
    """
    Arguments:
    * lato     * string, can be 'E','S','W' or 'N'
    * varname  * string,  is a PHYS variable : 'T','S','V'
    * timelist * is a list of date17 strings
    * Mask     * a `general.mask` object

    Returns :
       integer array Lon_Ind[nRivers] of Longitude Indexes
       integer array Lat_Ind[nRivers] of Latitude  Indexes
       float array  OUT[nRiver,nTimes] for the required variable
    """

    nFrames = len(timelist)
    nLato = 0
    for R in river_list:
        if R.side == lato: nLato = nLato + 1

    Lon_Ind = np.zeros((nLato), np.int32)
    Lat_Ind = np.zeros((nLato), np.int32)
    OUT = np.zeros((nLato, nFrames), np.float32)

    counter = 0
    for R in river_list:
        if R.side == lato:
            Lon_Ind[counter] = R.iLon - 1
            Lat_Ind[counter] = R.iLat - 1

            if varname == 'T':
                OUT[counter, :] = R.getTimeTemperature(timelist)
            if varname == 'S':
                OUT[counter, :] = R.sali
            if varname == 'V':
                denom = R.nHcells * Mask.CellArea(R.iLon,R.iLat, lato, R.nVcells)
                OUT[counter, :] = R.getTimeDischarge(timelist) / denom
            counter = counter + 1
    return Lon_Ind, Lat_Ind, OUT


def save_river_csv(river_list, variables, original_qmean=True,
                   output_path=None):
    field_associations = OrderedDict([
        ('N', 'ind'),
        ('freshwater source', 'name'),
        ('type of average', 'type_of_ave'),
        ('x (lon)', 'iLon'),
        ('y (lat)', 'iLat'),
        ('side', 'side'),
        ('vertical cells', 'nVcells'),
        ('horizontal cells', 'nHcells'),
        ('discharge', '_original_Q_mean')
    ])

    if not original_qmean:
        field_associations['discharge'] = 'Q_mean'

    dataset = {field: [] for field in field_associations}
    for bgc_var in variables:
        dataset[bgc_var.name] = []

    for river in river_list:
        for field_name, field_attr in field_associations.items():
            dataset[field_name].append(getattr(river, field_attr))
        for i, bgc_var in enumerate(variables):
            dataset[bgc_var.name].append(river.Conc[i])

    dataframe = pd.DataFrame(dataset)
    dataframe.set_index('N', inplace=True)
    return dataframe.to_csv(output_path, quoting=csv.QUOTE_NONNUMERIC)

import netCDF4 as nc
import numpy as np

dir = "C:/Users/smrTu/OneDrive/Documents/Workspace/Projects/CDIF-Dagstuhl/cdif/XrayAbsorbtion/"
filename = '20231120_002_1mg_Murchison_Smithsonian.cdf'

ds = nc.Dataset(dir + filename, 'r')

print(ds.variables.keys)

for dim in ds.dimensions.values():
 print(dim)

print('...............')

for var in ds.variables.values():
    print(var)
    print('.....')

for akey in ds.__dict__.keys():
    if ds.__dict__[akey]:
        print(f'{akey}: {ds.__dict__[akey]}')
    else:
        print(f'{akey}, no value')
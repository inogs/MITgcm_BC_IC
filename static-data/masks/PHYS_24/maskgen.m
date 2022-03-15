tmask = ncread('meshmask_INGVfor_ogstm.nc','tmask');
depth = ncread('meshmask_INGVfor_ogstm.nc','nav_lev');
lon = ncread('meshmask_INGVfor_ogstm.nc','nav_lon');
lat = ncread('meshmask_INGVfor_ogstm.nc','nav_lat');
umask = ncread('meshmask_INGVfor_ogstm.nc','umask');
vmask = ncread('meshmask_INGVfor_ogstm.nc','vmask');



%
nlon = size(tmask,1);
nlat = size(tmask,2);
nlev = size(tmask,3);
%

ncid = netcdf.create('mask.nc','CLOBBER');

%
nx = netcdf.defDim(ncid,'lon', nlon);
ny = netcdf.defDim(ncid,'lat',nlat);
nz = netcdf.defDim(ncid,'depth',nlev);
%
varid1 = netcdf.defVar(ncid,'lon','NC_FLOAT',nx);
netcdf.putAtt(ncid,varid1,'type','FLOAT'); 
varid2 = netcdf.defVar(ncid,'lat','NC_FLOAT',ny);
netcdf.putAtt(ncid,varid2,'type','FLOAT');       
varid3 = netcdf.defVar(ncid,'depth','NC_FLOAT',nz);
varid4 = netcdf.defVar(ncid,'tmask','NC_BYTE',[nx, ny, nz]);
varid5 = netcdf.defVar(ncid,'umask','NC_BYTE',[nx, ny, nz]);
varid6 = netcdf.defVar(ncid,'vmask','NC_BYTE',[nx, ny, nz]);


%
netcdf.endDef(ncid);

%
netcdf.putVar(ncid,varid1,lon(:,1));
netcdf.putVar(ncid,varid2,lat(1,:));
netcdf.putVar(ncid,varid3,depth(:,1));
netcdf.putVar(ncid,varid4,tmask);
netcdf.putVar(ncid,varid5,umask);
netcdf.putVar(ncid,varid6,vmask);
%
netcdf.close(ncid);

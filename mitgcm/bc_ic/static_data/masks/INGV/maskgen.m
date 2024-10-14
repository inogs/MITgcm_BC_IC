V=V4_mask;
N=ncread(V.maskfile,'nav_lev'); 

Depth=N.nav_lev;

% Lat,lon di origine  in gradi

S.DIMS.lon = 871; 
S.DIMS.lat = 253; 
S.DIMS.depth = numel(Depth); 

Lon= -18.125+(0:S.DIMS.lon-1)*1/16;
Lat= V.lat16; 

S.lon.value = Lon; 
S.lon.Attributes.type='FLOAT'; 

S.lat.value = Lat; 
S.lat.Attributes.type='FLOAT'; 

S.depth.value = Depth; 
S.depth.type = 'FLOAT'; 

ncwrite('mask.nc',S); 

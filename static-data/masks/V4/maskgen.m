%%
V=V4_mask;
%N=ncread(V.maskfile,'nav_lev','tmask'); 

Depth=N.nav_lev; 

% Lat,lon di origine  in gradi

S.DIMS.lon = V.jpi; 
S.DIMS.lat = V.jpj; 
S.DIMS.depth = numel(Depth); 

Lat = V.lat16; 
Lon = V.lon16;

S.lon.value = Lon; 
S.lon.Attributes.type='FLOAT'; 

S.lat.value = Lat; 
S.lat.Attributes.type='FLOAT'; 

S.depth.value = Depth; 
S.depth.type = 'FLOAT'; 

S.tmask.value = N.tmask; 
S.tmask.type  = 'BYTE'; 
ncwrite('mask.nc',S); 



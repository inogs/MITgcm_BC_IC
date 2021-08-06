% Lat,lon di origine  in gradi

Depth = 0; 
jpi = 70; 
jpj = 81; 
S.DIMS.depth = numel(Depth); 

Lon= 12.10550 + (0:jpi-1)*0.057 ;
Lat= 43.42000 + (0:jpj-1)*0.0395;


S.DIMS.Lon = jpi;
S.DIMS.Lat = jpj; 
S.lon.value = Lon; 
S.lon.Attributes.type='FLOAT'; 

S.lat.value = Lat; 
S.lat.Attributes.type='FLOAT'; 

S.depth.value = Depth; 
S.depth.type = 'FLOAT'; 



A=load('asogs_surfgeo_2014.asc');
tmask=double(~(reshape(A(:,3)>0,jpi,jpj))); 

S.tmask.value = tmask'; 
S.tmask.type = 'BYTE';

ncwrite('mask.nc',S); 

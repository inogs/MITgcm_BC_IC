
delZ= [ 1.500,   1.501,   3.234,   3.483,   3.750,   4.035,   4.339,   4.665,   5.012,   5.384, ...
       5.781,   6.206,   6.659,   7.144,   7.661,   8.215,   8.806,   9.437,  10.112,  10.833, ...
      11.603,  12.426,  13.305,  14.244,  15.247,  16.319,  17.463,  18.685,  19.990,  21.384, ...
      22.872,  24.461,  26.157,  27.968,  29.902,  31.965,  34.167,  36.517,  39.025,  41.700, ...
      44.554,  47.597,  50.843,  54.304,  57.994,  61.927,  66.107,  70.572,  75.328,  80.393, ...
      85.786,  91.526,  97.635, 104.134, 111.045, 118.392, 126.201, 134.496, 143.304, 152.654, ...
     162.574, 173.094, 184.243, 196.054, 208.559, 221.790, 235.779, 250.562, 266.170, 282.639, ...
     300.000, 318.288]; 


Depth=cumsum(delZ); 

% Lat,lon di origine  in gradi

V.jpi = 336; 
V.jpj = 512; 
V.jpk = numel(Depth); 


Lat = 30.171875 + (0:V.jpj-1)*1/32; 
Lon = 12.234375 + (0:V.jpi-1)*1/32;

%% tmask construction
fid = fopen('bathy','r'); 
Bathy=-fread(fid, [V.jpi V.jpj], 'float32'); 
fclose(fid);



LEVELS=zeros(V.jpi, V.jpj); 

for ji = 1:V.jpi
    for jj= 1:V.jpj
        if Bathy(ji,jj) == 0,
            LEVELS(ji,jj) = 0;
        else
            for jk = 1:V.jpk
                if Depth(jk) >= Bathy(ji,jj); 
                    break
                end
            end
            LEVELS(ji,jj)=jk;
        end        
    end
end

tmask = zeros(V.jpk,V.jpj,V.jpi); 
for ji = 1:V.jpi
    for jj= 1:V.jpj
        tmask(1:LEVELS(ji,jj), jj, ji ) = 1; 
    end
end


%%

S.DIMS.lon   = V.jpi;
S.DIMS.lat   = V.jpj; 
S.DIMS.depth = V.jpk; 

S.lon.value = Lon; 
S.lon.Attributes.type='FLOAT'; 

S.lat.value = Lat; 
S.lat.Attributes.type='FLOAT'; 

S.depth.value = Depth; 
S.depth.type = 'FLOAT'; 

S.tmask.value = tmask; 
S.tmask.type = 'BYTE';

 ncwrite('mask.nc',S); 
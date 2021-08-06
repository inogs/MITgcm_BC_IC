
delZ= [1.500,  1.501,  3.234,  3.483,  3.750,  4.035,  4.339,  4.665,  5.012,  5.384, ...
       5.781,  6.206,  6.659,  7.144,  7.661,  8.215,  8.806,  9.437, 10.112, 10.833, ...
      11.603, 12.426, 13.305, 14.244, 15.247, 16.319, 17.463] ;

CellBottoms=cumsum(delZ);
Depth = CellBottoms - delZ/2 ;

% Lat,lon di origine  in gradi

V.jpi = 494; 
V.jpj = 300; 
V.jpk = numel(Depth); 


Lat = 43.47265625 + (0:V.jpj-1)*1/128; 
Lon = 12.22265625 + (0:V.jpi-1)*1/128;

%% tmask construction
fid = fopen('bathy','r'); 
Bathy=fread(fid, [V.jpi V.jpj], 'float32'); 
fclose(fid);

ii=Bathy>0; 
Bathy(ii) = Bathy(ii)-1.4e-07 ; 

LEVELS=zeros(V.jpi, V.jpj); 

for ji = 1:V.jpi
    for jj= 1:V.jpj
        if Bathy(ji,jj) == 0,
            LEVELS(ji,jj) = 0;
        else
            for jk = 1:V.jpk
                if CellBottoms(jk) >= Bathy(ji,jj); 
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

S.CellBottoms.value = CellBottoms;
S.CellBottoms.type = 'FLOAT';

S.tmask.value = tmask; 
S.tmask.type = 'BYTE';

 ncwrite('mask.nc',S); 

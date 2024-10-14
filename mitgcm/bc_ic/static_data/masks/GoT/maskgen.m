
V.jpi = 196; 
V.jpj = 135; 
V.jpk =  40; 

Lat =45.3734375  + (0:V.jpj-1)*1/320; 
Lon =13.2140625  + (0:V.jpi-1)*1/320;

%% tmask construction
fid = fopen('bathy','r'); 
Bathy=-fread(fid, [V.jpi V.jpj], 'float32'); 
fclose(fid);

Depth = [0.25:0.5:2.75 3.5:1:31.50 33:2:39 41.5];

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
S.DIMS.lon = V.jpi;
S.DIMS.lat = V.jpj;
S.DIMS.Depth = V.jpk;


S.lon.value = Lon; 
S.lon.Attributes.type='FLOAT'; 

S.lat.value = Lat; 
S.lat.Attributes.type='FLOAT'; 

S.depth.value = Depth; 
S.depth.type = 'FLOAT'; 

S.tmask.value = tmask; 
S.tmask.type = 'BYTE';

ncwrite('mask.nc',S); 










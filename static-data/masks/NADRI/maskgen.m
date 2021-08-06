
V=V1_mask; % soon modified
N=ncread(V.maskfile,'nav_lev'); 

Depth=[N.nav_lev(1)/2; N.nav_lev(1)*1.5; N.nav_lev(2:26)]; 

% Lat,lon di origine  in gradi

V.jpi = 240; 
V.jpj = 148; 
V.jpk = numel(Depth); 

Lat = 43.5390625 + (0:V.jpj-1)*1/64; 
Lon = 12.2265625 + (0:V.jpi-1)*1/64;

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



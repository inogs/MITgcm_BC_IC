
%delZ= [1.500,  1.501,  3.234,  3.483,  3.750,  4.035,  4.339,  4.665,  5.012,  5.384, ...
%       5.781,  6.206,  6.659,  7.144,  7.661,  8.215,  8.806,  9.437, 10.112, 10.833, ...
%      11.603, 12.426, 13.305, 14.244, 15.247, 16.319, 17.463] ;

delZ= [1.500,   1.501,   3.234,   3.483,   3.750,   4.035,   4.339,   4.665,   5.012,   5.384,...
       5.781,   6.206,   6.659,   7.144,   7.661,   8.215,   8.806,   9.437,  10.112,  10.833,...
      11.603,  12.426,  13.305,  14.244,  15.247,  16.319,  17.463,  18.685,  19.990,  21.384,...
      22.872,  24.461,  26.157,  27.968,  29.902,  31.965,  34.167,  36.517,  39.025,  41.700,...
      44.554,  47.597,  50.843,  54.304,  57.994,  61.927,  66.107,  70.572,  75.328,  80.393,...
      85.786,  91.526,  97.635, 104.134, 111.045, 118.392, 126.201, 134.496, 143.304, 152.654,...
     162.574, 173.094];

CellBottoms=cumsum(delZ);
Depth = CellBottoms - delZ/2 ;

% Lat,lon di origine  in gradi

V.jpi = 360;	% 494; 
V.jpj = 204;	% 300; 
V.jpk = numel(Depth); % 52


%Lat = 43.47265625 + (0:V.jpj-1)*1/128; 
%Lon = 12.22265625 + (0:V.jpi-1)*1/128;

Lat = 40.84765625 + (0:V.jpj-1)*1/128; 
Lon = 11.28515625 + (0:V.jpi-1)*1/128;

%% tmask construction
fid = fopen('bathy_AZA_Lazio.bin','r'); 
Bathy=fread(fid, [V.jpi V.jpj], 'float32'); 
fclose(fid);
Bathy=Bathy *-1.0;

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

%tmask = zeros(V.jpk,V.jpj,V.jpi); 
tmask = zeros(V.jpi,V.jpj,V.jpk); % FIXME
for ji = 1:V.jpi
    for jj= 1:V.jpj
        %tmask(1:LEVELS(ji,jj), jj, ji ) = 1; 
        tmask(ji, jj, 1:LEVELS(ji,jj)) = 1; % FIXME
    end
end


ncid = netcdf.create('mask.nc','CLOBBER');

%
nx = netcdf.defDim(ncid,'lon', V.jpi);
ny = netcdf.defDim(ncid,'lat',V.jpj);
nz = netcdf.defDim(ncid,'depth',V.jpk);
%
varid1 = netcdf.defVar(ncid,'lon','NC_FLOAT',nx);
netcdf.putAtt(ncid,varid1,'type','FLOAT'); 
varid2 = netcdf.defVar(ncid,'lat','NC_FLOAT',ny);
netcdf.putAtt(ncid,varid2,'type','FLOAT');       
varid3 = netcdf.defVar(ncid,'depth','NC_FLOAT',nz);
varid5 = netcdf.defVar(ncid,'CellBottoms','NC_FLOAT',nz);
varid4 = netcdf.defVar(ncid,'tmask','NC_BYTE',[nx, ny, nz]);


%
netcdf.endDef(ncid);

%
netcdf.putVar(ncid,varid1,Lon');
netcdf.putVar(ncid,varid2,Lat);
netcdf.putVar(ncid,varid3,Depth');
netcdf.putVar(ncid,varid5,CellBottoms');
netcdf.putVar(ncid,varid4,tmask);
%
netcdf.close(ncid);


% FIXME: aggiunto CellBottoms 

%%
%{
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
%}



'''===========================================================================================================
Universidade Federal de Santa Catarina (UFSC)
Programa de Pós-Graduação em Engenharia Ambiental (PPGEA)
Autor: Otávio Nunes dos Santos
Orientador: Dr. Leonardo Hoinaski

Artigo Científico: Identificação das fontes de contaminação da água de chuva do município de Florianópolis-SC.                             
===========================================================================================================''' 

#%% ---------------------- Importação de bibiotecas
import os
import glob    
import pandas as pd  
import numpy as np  
import xarray as xr
import geopandas as gpd
from termcolor import colored
from shapely.geometry import Polygon
import shapely.vectorized as sv
import rioxarray
from shapely.geometry import mapping
from datetime import datetime, timedelta

#%% ---------------------- Cálculo de concentração nas trajetórias de massa de ar

class Trajectory_Conc:
    
    def __init__(self, pathMERRA, rs, pathTrajs, pol, typeCol, dateIn, dateFin):
        self.pathMERRA = pathMERRA
        self.pathTrajs = pathTrajs
        self.dateIn = dateIn
        self.dateFin = dateFin
        self.rs = rs
        self.pol = pol
        self.typeCol = typeCol

# ---  Checagem dos dados de trajetória  
         
    def ChecagemArquivos(self):      
        
        def Check1():
            idx = pd.DataFrame(index = pd.date_range(self.dateIn+'-01-01 00:00:00', 
                                                     self.dateFin+'-12-31 00:00:00'))
            trajsDays = [traj.split('.')[0] for traj in os.listdir(self.pathTrajs)]
            trajsDay = pd.DataFrame(index = pd.to_datetime(trajsDays))
            trajsDay['mask'] = 'datas ok!!!'
            validacao = idx.join(trajsDay)
            validacao = validacao.reset_index()
            if len(np.where(validacao.isna())[0]) > 0:
                missVal = validacao.loc[np.where(validacao.isna())[0].item()]['index']
                if missVal: print(colored('\nDados faltantes: %s'%missVal), 'red')
                value = input("\nOs arquivos HYSPLIT foram corretamente baixados? (s, n): ")
                if value == 'não': print('\nBaixar as trajetórias dos dias indicados acima.')
            else: print(colored('\nTodas as trajetórias foram baixadas corretamente!!!', 'green'))
            return trajsDays
        
        def Check2():
            cols = {2:'ano', 3:'mes', 4:'dia', 5:'hora', 8:'horaRev', 9:'latitude', 10:'longitude', 
                    11: 'Starting leve (m)', 12: 'Pressure (kPa)', 13: 'THETA', 14: 'AIR_TEMP (K)', 
                    15: 'RAINFALL (mm/h)', 16:'MIXDEPTH (m)', 17:'RELHUMID (%)', 18:'TERR_HEIGHT (m)', 
                    19:'SUN_FLUX (W/m²)'}
         
            files = []
            for file in os.listdir(self.pathTrajs):
                trajFile = pd.read_fwf(self.pathTrajs+'/'+file, header = None, 
                                       skiprows= len(pd.read_fwf(self.pathTrajs+'/'+file))-72, 
                                       usecols = cols.keys(), names = cols.values())
                dateFormat = ['20'+str(ano)+str(mes).rjust(2, '0')+str(dia).rjust(2, '0')+str(hora).rjust(2, '0') 
                              for ano, mes, dia, hora in zip(trajFile.ano, trajFile.mes, trajFile.dia, trajFile.hora)]  
                trajFile['dateFormat'] = dateFormat
                
                files.append(trajFile)
                           
            datas = ['20'+str(date.ano[0])+str(date.mes[0]).rjust(2, '0')+str(date.dia[0]).rjust(2, '0') 
                     for date in files]             
            datasRep = list(set([int(x) for x in datas if datas.count(x) > 1])) 
            if len(datasRep) > 0:
                print('\nVerificar arquivos, datas estão duplicadas em: ')
                datasRep.sort()
                for p in datasRep: print(colored(p, 'red')) 
            return datas, files

        def Check3(trajDays, datas):
            if trajDays==datas: print(colored('\nValidação concluída!!! ', 'green'))
        
        trajDays = Check1()
        datas, files = Check2()
        Check3(trajDays, datas)
        return files

# ---  Definição do domínio de modelagem com base no alcance
#      do conjunto de trajetórias   
  
    def Coords_MERRA2(self, trajs_list):
        trajs = pd.concat(trajs_list)
        xmin = min(trajs.longitude); xmax = max(trajs.longitude)
        ymin = min(trajs.latitude); ymax = max(trajs.latitude)        
        return xmin, xmax, ymin, ymax 
    
# ---  Definição dos 4 arquivos .nc do MERRA-2
#      para casa pto de trajetória (73h)
        
    def Extract_MERRA2(self, datas, band):         
        
        file_0H = datas
        file_0H = 'MERRA-2/'+self.rs+'/'+self.pol+'/MERRA2_400.tavg1_2d_'+self.typeCol+'_Nx.'+file_0H+'.nc4.nc4'
        day_0h = xr.open_dataset(file_0H)[band][:]
        print(file_0H)
        
        file_24H = (pd.to_datetime(datas) - timedelta(hours=24)).strftime('%Y%m%d')
        file_24H = 'MERRA-2/'+self.rs+'/'+self.pol+'/MERRA2_400.tavg1_2d_'+self.typeCol+'_Nx.'+file_24H+'.nc4.nc4'
        day_24h = xr.open_dataset(file_24H)[band][:]
        print(file_24H)
        
        file_48H = (pd.to_datetime(datas) - timedelta(hours=48)).strftime('%Y%m%d')
        file_48H = 'MERRA-2/'+self.rs+'/'+self.pol+'/MERRA2_400.tavg1_2d_'+self.typeCol+'_Nx.'+file_48H+'.nc4.nc4'
        day_48h = xr.open_dataset(file_48H)[band][:]
        print(file_48H)
        
        file_72H = (pd.to_datetime(datas) - timedelta(hours=72)).strftime('%Y%m%d')
        file_72H = 'MERRA-2/'+self.rs+'/'+self.pol+'/MERRA2_400.tavg1_2d_'+self.typeCol+'_Nx.'+file_72H+'.nc4.nc4'
        day_72h = xr.open_dataset(file_72H)[band][:]
        print(file_72H)
        
        mergedConc = xr.merge([day_0h, day_24h,day_48h, day_72h])   
        mergedConc = mergedConc[band][:73]
        return mergedConc

# ---  Utilização dos campos de concentração de poluentes MERRA-2
    
    def Grid_MERRA2(self, band):        
        
        file = glob.glob(self.pathMERRA+self.rs+'/'+self.pol+'/*.nc4')[0]
        nc4_files = xr.open_dataset(file)
        nc4_files.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
        nc4_files.rio.write_crs("epsg:4326", inplace=True)    
        
        trajet = self.ChecagemArquivos().copy()
        trajet = pd.concat(trajet, ignore_index = True)
        trajet = gpd.GeoDataFrame(trajet, crs = 'EPSG:4326', 
                                  geometry=gpd.points_from_xy(trajet.longitude, trajet.latitude))
        
        clipped = nc4_files.rio.clip(trajet.geometry.apply(mapping), trajet.crs, drop=True)
        
        co = np.array(clipped[band][0]).flatten()
        lon, lat = np.meshgrid(clipped['lon'], clipped['lat']) 
        lon = lon.flatten(); lat = lat.flatten()
        coords = pd.DataFrame({self.pol:co, 'lon':lon, 'lat':lat}).dropna()       

        spatialX = 0.625/2; spatialY = 0.5/2
        maskGeoMerra = gpd.GeoDataFrame(geometry = [Polygon([(x - spatialX, y - spatialY), 
                                                     (x - spatialX, y + spatialY), 
                                                     (x + spatialX, y + spatialY), 
                                                     (x + spatialX, y - spatialY)]) 
                                                    for x, y in zip (coords.lon, coords.lat)], crs = 'EPSG:4326')
                       
        return maskGeoMerra

# ---  Separando trajetórias totais das associadas a eventos de poluição
        
    def Trajetorias_Threshold(self, traj_n, eventosPoluidos):        
        dates = pd.DataFrame(index = [pd.to_datetime(traj.split('.')[0]) for traj in os.listdir(self.pathTrajs)])
        mask = dates.join(eventosPoluidos).reset_index().dropna()
        trajs_Thres = [traj_n[idx] for idx in list(mask.index)] 
        return trajs_Thres    
  
# ---  Cálculo da concentração de poluentes nas trajetórias

    def fromMERRA_toTrajs(self, trajs_list, band):        
        dados = []        

        for idx, traj in enumerate(trajs_list): 
            datas = '20'+str(traj.ano[0])+str(traj.mes[0]).rjust(2, '0')+str(traj.dia[0]).rjust(2, '0')
            print(colored('\nCarregando Trajetória %s de %s: %s' %(idx, len(trajs_list), datas), 'red'))
 
            merra = self.Extract_MERRA2(datas, band) 
            traj = traj.reset_index(drop = True)
            mask = [np.array(merra[i].sel(lat = traj.latitude[i], lon=traj.longitude[i], method="nearest")) for 
                    i in range(0, len(traj))]            
            traj['Concentration'] = mask
            traj['Concentration'] = traj['Concentration'].astype(float)
            dados.append(traj)   

        return dados
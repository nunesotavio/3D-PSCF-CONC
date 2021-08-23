'''===============================================================================================================
Federal University of Santa Catarina
Department of Sanitary and Environmental Engineering
Authors: Otávio Nunes dos Santos, Leonardo Hoinaski
Incorporating gridded concentration data in air pollution back trajectories analysis for source identification
==================================================================================================================''' 

#%% ---------------------- Importação de bibiotecas
import os
import glob    
import pandas as pd  
import numpy as np  
import xarray as xr
import geopandas as gpd
from datetime import datetime, timedelta
import shapely.vectorized as sv

#%%

class Method_3DPSCF_CONC:
    
    def __init__(self, traj_n, traj_m, grid):
        self.traj_n = traj_n
        self.traj_m = traj_m
        self.grid = grid
               
    def Analisys_3D(self):
        
        # ----- grid_n
        traj_nTotal = pd.concat(self.traj_n, ignore_index = True)
        traj_nTotal = traj_nTotal[traj_nTotal['Starting leve (m)'] < traj_nTotal['MIXDEPTH (m)']]
        traj_nTotal = gpd.GeoDataFrame(traj_nTotal, crs = 'EPSG:4326', geometry=gpd.points_from_xy(traj_nTotal.longitude, traj_nTotal.latitude))
        
        # ----- grid_m
        traj_mTotal = pd.concat(self.traj_m, ignore_index = True)
        traj_mTotal = gpd.GeoDataFrame(traj_mTotal, crs = 'EPSG:4326', geometry=gpd.points_from_xy(traj_mTotal.longitude, traj_mTotal.latitude))
        traj_mTotal = traj_mTotal[traj_mTotal['Starting leve (m)'] < traj_mTotal['MIXDEPTH (m)']]
        
        return traj_nTotal, traj_mTotal


    def PSCF_3DCONC(self, traj_nTotal, traj_mTotal):
         
        # ----- Cálculo do tempo de residência total 
        #       do conjuntos de trajetórias sobre as células da grade
        
        grid_n = gpd.sjoin(self.grid, traj_nTotal)
        grid_n.reset_index(inplace = True)
        grid_n = grid_n.groupby('index').agg({'RAINFALL (mm/h)': 'mean', 'index': 'count', 'Concentration':'mean', 'geometry':'first'})
        grid_n = gpd.GeoDataFrame(grid_n).rename(columns = {'index':'Residence_n', 'Concentration':'Concentration_n'}).reset_index(drop = True)
        
        # ----- Cálculo do tempo de residência do conjunto de trajetórias 
        #       associado a eventos de poluição sobre as células da grade
        
        grid_m = gpd.sjoin(self.grid, traj_mTotal)
        
        grid_m['hRevs'] = [(datetime.strptime(dates, '%Y%m%d%H') - timedelta(hours = (2*int(hour)\
                           - int(hoursRev)))).strftime('%Y%m%d%H') for dates, hoursRev, 
                           hour in zip(grid_m.dateFormat, grid_m.horaRev, grid_m.hora)]
            
        traj_hRev = pd.concat(traj_nTotal)
        gridRev = traj_hRev[traj_hRev['dateFormat'].isin(grid_m['hRevs'])].loc[0]
        gridRev= gridRev.rename(columns = {'dateFormat':'hRevs'})
        
        grid_m = pd.merge(grid_m, gridRev, how = 'left', on = 'hRevs', indicator=True).set_index(grid_m.index)
          
        grid_m.reset_index(inplace = True)
        grid_m = grid_m.groupby('index').agg({'RAINFALL (mm/h)_x': 'mean', 'index': 'count', 'Concentration_x':'mean', 'Concentration_y':'mean',
                                              'geometry':'first'})
        grid_m = gpd.GeoDataFrame(grid_m).rename(columns = {'index':'Residence_m', 'Concentration_x':'Concentration_m',
                                                            'Concentration_y':'Concentration_rs', 'RAINFALL (mm/h)_x':'RAINFALL (mm/h)_m'}).reset_index(drop = True)
        
        # ----- PSCF-3D-CONC
        pscf3DCONC = pd.merge(grid_n, grid_m, on = 'geometry')
        
        pscf3DCONC['W(i,j)'] = 0.0
        
        # ----- Weighted_func
                
        n_ave = np.mean(grid_n['Residence_n'])
        for idx in range(0, len(pscf3DCONC)):
            if pscf3DCONC['Residence_n'][idx] > 3*n_ave: pscf3DCONC['W(i,j)'][idx] = 1
            if 3*n_ave > pscf3DCONC['Residence_n'][idx] > 1.5*n_ave: pscf3DCONC['W(i,j)'][idx] = 0.7
            if 1.5*n_ave > pscf3DCONC['Residence_n'][idx] > n_ave: pscf3DCONC['W(i,j)'][idx] = 0.4
            if n_ave > pscf3DCONC['Residence_n'][idx]: pscf3DCONC['W(i,j)'][idx] = 0.1                    
    
        pscf3DCONC['Concentration_m'] = np.where(pscf3DCONC['Concentration_m'] > pscf3DCONC['Concentration_rs'], 
                                                 pscf3DCONC['Concentration_rs'], pscf3DCONC['Concentration_m'])
       
        pscf3DCONC['3D-PSCF-CONC'] = ((pscf3DCONC['Residence_m']*pscf3DCONC['Concentration_m'])/
                                     (pscf3DCONC['Residence_n']*pscf3DCONC['Concentration_rs']))*pscf3DCONC['W(i,j)']
        
       
        print(colored('******* PROCESSO FINALIZADO: '+id_pscf+ ' *******', 'red'))
        
        return pscf3DCONC


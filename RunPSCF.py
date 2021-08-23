'''===============================================================================================================
Federal University of Santa Catarina
Department of Sanitary and Environmental Engineering
Authors: Otávio Nunes dos Santos, Leonardo Hoinaski
Incorporating gridded concentration data in air pollution back trajectories analysis for source identification
==================================================================================================================''' 

#%% ---------------------- Import of modules
from webScrapping import Hysplit_Scrap
from trajConc import Trajectory_Conc
from PSCF_METHOD import Method_3DPSCF_CONC
from Threshold_analysis import PSCF_Threshold

#%% ---------------------- Module importation PSCF_Threshold
# ---- Definition of pollution events

threshold_date = PSCF_Threshold('CETESB/co.csv', 'CO').Threshold_date()

#%% ---------------------- Module importation Hysplit_Scrap
# ---- Back trajectories converging to air pollution station
webScrap = Hysplit_Scrap("-23.518", "-46.743", 'trajetoriasSP')
webScrap.runHysplit()

#%% ---------------------- Module importation Trajectory_Conc
dadosTraj = Trajectory_Conc('MERRA-2/', 'SP', 'trajetoriasSP', 'CO', 'chm', '2015', '2019')

# --- Checking the download of back trajectories
traj_n = dadosTraj.ChecagemArquivos()

# --- Gridded dimension (MERRA-2)
coordsMERRA = dadosTraj.Coords_MERRA2(traj_n) # xmin, xmax, ymin, ymax
gridMERRA = dadosTraj.Grid_MERRA2('COSC')

# --- Pollutant concentration in back trajectories
traj_n = dadosTraj.fromMERRA_toTrajs(traj_n, 'COSC')
traj_m = dadosTraj.Trajetorias_Threshold(traj_n, threshold_date)

#%% ---------------------- Module importation Method_3DPSCF_CONC
contribuicoes = Method_3DPSCF_CONC(traj_n, traj_m, gridMERRA)

# --- Select back trajectories - threshold height
traj_n3D, traj_m3D = contribuicoes.Analisys_3D()

# --- 3D-PSCF-CONC
pscf3DCONC = contribuicoes.PSCF_3DCONC(traj_n3D, traj_m3D)



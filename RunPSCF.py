'''===========================================================================================================
Universidade Federal de Santa Catarina (UFSC)
Programa de Pós-Graduação em Engenharia Ambiental (PPGEA)
Autor: Otávio Nunes dos Santos
Orientador: Dr. Leonardo Hoinaski

Artigo Científico: Identificação das fontes de contaminação da água de chuva do município de Florianópolis-SC.                             
===========================================================================================================''' 

#%% ---------------------- Importação dos módulos
from webScrapping import Hysplit_Scrap
from trajConc import Trajectory_Conc
from PSCF_METHOD import Method_3DPSCF_CONC
from Threshold_analysis import PSCF_Threshold
a
#%% ---------------------- Importação da Classe PSCF_Threshold

# ---- Definição dos eventos de poluição

threshold_date = PSCF_Threshold('CETESB/co.csv', 'CO').Threshold_date()

#%% ---------------------- Importação da Classe Hysplit_Scrap

# ---- Dados de trajetória convergindo para Marginal Tietê-Ponte Remédios
webScrap = Hysplit_Scrap("-23.518", "-46.743", 'trajetoriasSP')
webScrap.runHysplit()


#%% ---------------------- Importação da Classe Trajectory_Conc

dadosTraj = Trajectory_Conc('MERRA-2/', 'SP', 'trajetoriasSP', 'CO', 'chm', '2015', '2019')

# --- Checagem do download das trajetórias
traj_n = dadosTraj.ChecagemArquivos()

# --- Definição das dimensões do domínio do campo de concentração (MERRA-2)
coordsMERRA = dadosTraj.Coords_MERRA2(traj_n) # xmin, xmax, ymin, ymax
gridMERRA = dadosTraj.Grid_MERRA2('COSC')

# --- Cálculo de concentração de poluentes nas trajetórias de massa de ar
traj_n = dadosTraj.fromMERRA_toTrajs(traj_n, 'COSC')
traj_m = dadosTraj.Trajetorias_Threshold(traj_n, threshold_date)

#%% ---------------------- Importação da Classe Method_3DPSCF_CONC

contribuicoes = Method_3DPSCF_CONC(traj_n, traj_m, gridMERRA)

# --- Selecionando as trajetórias a partir da altura de injeção de poluentes
traj_n3D, traj_m3D = contribuicoes.Analisys_3D()

# --- Calculando as contribuições pelo método 3D-PSCF-CONC
pscf3DCONC = contribuicoes.PSCF_3DCONC(traj_n3D, traj_m3D)



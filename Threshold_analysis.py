
#%% ---------------------- Importação de bibiotecas
import glob    
import pandas as pd  
import numpy as np  

#%% ---------------------- Dados de concentração de CO - Enseada de Suá (Espírito Santo)

class PSCF_Threshold:
    
    def __init__(self, file, pol):
        self.file = file
        self.pol = pol
    
    def Threshold_date(self):
        
        # ---- Upload dos dados
        dados = pd.concat([pd.read_csv(file, delimiter = ';') for file in glob.glob(self.file)], ignore_index = True)
        dados['Hora'] = np.where(dados['Hora'] == '24:00:00', '00:00:00', dados['Hora'])
        dados['Data'] = pd.to_datetime(dados['Data']+ ' '+dados['Hora'])
        dados = dados.sort_values(by = 'Data')
        
        dados = dados[['Data', self.pol]]
        dados = dados.set_index('Data')
        dados_daily = dados.resample('D').mean()  # Threshold definido como a média diária do período 
        
        # ---- Definição do threshold para eventos poluídos
        eventosPoluidos = dados_daily[dados_daily[self.pol] > dados_daily[self.pol].mean()]
        eventosPoluidos = dados_daily.loc[eventosPoluidos.index]
        eventosPoluidos['Date'] = [str(data.year)+str(data.month).rjust(2, '0')+str(data.day).rjust(2, '0')
                                   for data in eventosPoluidos.index]
        
        datas = eventosPoluidos.groupby('Date').agg({'Date': 'first'})
        return datas

'''===========================================================================================================
Universidade Federal de Santa Catarina (UFSC)
Programa de Pós-Graduação em Engenharia Ambiental (PPGEA)
Autor: Otávio Nunes dos Santos
Orientador: Dr. Leonardo Hoinaski

Artigo Científico: Identificação das fontes de contaminação da água de chuva do município de Florianópolis-SC.                             
===========================================================================================================''' 

#%% ------------------------------------ Importação de bibiotecas
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

#%%
# --------- Download dos dados de trajetórias do site NOAA 

class Hysplit_Scrap:
    
    def __init__(self, latitude, longitude, downloadFolder):        
        self.latitude = latitude
        self.longitude = longitude
        self.downloadFolder = downloadFolder
     
    def runHysplit(self):
        webdriver = self.ConfiguracaoWebDriver()   
        driverURL = self.Conexao_NOAA(webdriver)
        gdas = self.Obter_gdasFile(driverURL)
        self.Download_dados(gdas, driverURL)
                     
    def ConfiguracaoWebDriver(self):        
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("--incognito")
        prefs = {"download.default_directory" : self.downloadFolder}
        chromeOptions.add_experimental_option("prefs",prefs)  
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chromeOptions)
        return driver
    
    def Conexao_NOAA(self, driver):
        driver.get('https://www.ready.noaa.gov/hypub-bin/trajasrc.pl')
        lat = driver.find_element_by_id("LatId")
        lat.send_keys(self.latitude)
        lon = driver.find_element_by_id("LonId")
        lon.send_keys(self.longitude)
        driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/div[2]/form/div/div/table[2]/tbody/tr[1]/td[2]/select/option[2]").click()
        driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/div[2]/form/div/center/input[2]").click()
        return driver
        
    def Obter_gdasFile(self, driver):
        gdas = driver.find_element_by_name("mfile")
        mask = [word.strip().split(' ')[0] for word in list(gdas.text.split('\n'))]
        mask = mask[mask.index('gdas1.dec19.w5'):mask.index('gdas1.feb19.w3')+1]
        mask.reverse()
        return mask 
         
    def Inputs_Hysplit(self, driver, ano, mes ,dia, meteoCheck):        
        year = driver.find_element_by_name("Start year")
        year.send_keys(ano)        
        month = driver.find_element_by_name("Start month")
        month.send_keys(mes)        
        day = driver.find_element_by_name("Start day")
        day.send_keys(dia)     
        hora = driver.find_element_by_name("Start hour")
        hora.send_keys("00") # trajetórias chegando ao local receptor meia noite (00:00)        
        duracao = driver.find_element_by_name("duration")
        duracao.clear()
        duracao.send_keys("72") # duracao da trajtórias de 72horas       
        driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[10]/td[3]/input").click()
        
        # --- Selecionar variáveis meteorológicas:
        if meteoCheck == True:            
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[25]/td[2]/input[1]").click()
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[25]/td[2]/input[2]").click()
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[25]/td[2]/input[3]").click()
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[25]/td[2]/input[4]").click()
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[25]/td[2]/input[5]").click()
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[25]/td[2]/input[6]").click()
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[3]/table[2]/tbody/tr[25]/td[2]/input[7]").click()
        
        driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/table/tbody/tr/td/input").click()
        
    def Outputs_Hysplit(self, driver, ano, mes ,dias, meteoCheck):        
        self.Inputs_Hysplit(driver, ano, mes ,dias, meteoCheck)             
        objetoXpath = "/html/body/div/table/tbody/tr/td/div[4]/table[1]/tbody/tr/td/font/ul/li[2]/b/a"
        outputFile = EC.presence_of_element_located((By.XPATH, objetoXpath))
        WebDriverWait(driver, 60).until(outputFile)       
        outputFile = driver.find_element_by_xpath(objetoXpath).get_attribute("href")
        file = "http://www.ready.noaa.gov"+outputFile.split("'")[1]
        
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(file)
        content = driver.page_source
        soup = BeautifulSoup(content, "html.parser") 
        
        f = open(self.downloadFolder+'/'+ano+mes+dias+'.txt','a')
        f.write(soup.text)
        f.close() 
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        driver.back()  
        
    def Download_dados(self, datesWeek, driver):
        for files in datesWeek:  
            meteoCheck = True
            print('\n'+files)
            gdas = driver.find_element_by_name("mfile")  
            gdas.send_keys(files) 
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/center/input").click()
            driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/div[4]/form/div[2]/table[1]/tbody/tr[2]/td[2]/input").click()                   
            dias = driver.find_element_by_name("Start day")
            dias = [word.strip().split(' ')[0] for word in list(dias.text.split('\n'))]
            ano = ['20'+driver.find_element_by_name("Start year").get_attribute("value")]*len(dias)
            mes = [driver.find_element_by_name("Start month").get_attribute("value")]*len(dias)                   
            for idx in range(0, len(dias)):                
                self.Outputs_Hysplit(driver, ano[idx], mes[idx] ,dias[idx], meteoCheck)   
                print(dias[idx]+'/'+mes[idx]+'/'+ano[idx])                    
                meteoCheck = False
            driver.back() 
            

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException, ElementNotInteractableException, InvalidArgumentException
import time
import pickle
from os import listdir

path = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/Beyond Trust/Data Uploads Test_2' #ONLY CSV FILES THAT YOU WANT TO LOAD SHOULD BE IN THIS PATH
logpath = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/Beyond Trust/log.txt'
winpath = "C:\\Users\\E075882\\OneDrive - RSM\\All Data\\Client\\Beyond Trust\\Data Uploads Test_2\\"
savedimport = "https://1085563-sb1.app.netsuite.com/app/setup/assistants/nsimport/importassistant.nl?recid=20&new=T"
unloadedfiles = []
loadedfiles = []
myfiles =  listdir(path)
options = Options()
#options.add_argument("--headless")

driver = webdriver.Firefox(options=options)
driver.get(savedimport)
driver.maximize_window()
cookies = pickle.load(open("cookies.pkl", "rb"))
for cookie in cookies:
    #cookie['domain'] = 
    try:
        driver.add_cookie(cookie)
    except Exception as e:
        print(e)
        pass   

i = 0
j = 0
#start loop to load all files from selected folder
while i < len(myfiles):
    driver.get(savedimport)

    #start upload process
    #select file from folder
    loadfile = myfiles[i] 
    WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="next"]')))
    time.sleep(.5)

    driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(winpath + loadfile)
    time.sleep(.5)

    #go to next page after selecting file
    btn = driver.find_element(By.XPATH, '//input[@id="next"]')
    btn.click()

    #wait for loading....
    WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="next"]')))
    time.sleep(.5)

    #enable multithreading
    btn = driver.find_element(By.XPATH, '//td[@id="label_fldarr_1"]')
    btn.click()
    time.sleep(.5)

    #find all checkboxes and select multi threading
    btn = driver.find_elements(By.XPATH, '//img[@class="checkboximage"]')
    btn[5].click()
    time.sleep(.5)

    #go to next page
    btn = driver.find_element(By.XPATH, '//input[@id="next"]')
    btn.click()

    #go to next page
    WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="secondarynext"]'))).click()

    #hover and click run
    #if there is an issue with the file, log it
    #if runs successfully, add success event to log
    try:
        
        btn =  driver.find_element(By.XPATH, '//td[@class="bntBgB multiBnt"]')
        ActionChains(driver).move_to_element(btn).perform()
        time.sleep(1)
        run = driver.find_elements(By.XPATH, '//td[@class="ddmText"]')
        #run.click()
        ActionChains(driver).move_to_element(run[1]).click().perform()
        time.sleep(.5)
        Alert(driver).accept()
        loadedfiles.append
        print(f'file number {i} loaded ({loadfile})\n')
        with open(logpath, 'a') as f:
            f.write(f'file number {i} loaded ({loadfile})\n')
        time.sleep(3)
        j += 1
    except Exception as e:
        unloadedfiles.append(loadfile)
        print(f'file number {i} NOT loaded ({loadfile})\n')
        with open(logpath, 'a') as f:
            f.write(f'file number {i} NOT loaded ({loadfile})\n')

    if i == len(myfiles) - 1:
        print(f'program complete\n{j}/{len(myfiles)} loaded succesfully')
        driver.quit()
        with open(logpath, 'a') as f:
            f.write(f'\n{j}/{len(myfiles)} loaded succesfully')
    i += 1

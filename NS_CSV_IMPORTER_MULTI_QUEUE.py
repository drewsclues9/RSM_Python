from selenium import webdriver

from selenium.webdriver.firefox.service import Service

from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.common.by import By

from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.alert import Alert

from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException, ElementNotInteractableException, TimeoutException

import time

import pickle

from os import listdir



path = 'C:/Users/arichards/Documents/Autoloader/Data Files/GLEntry' #ONLY CSV FILES THAT YOU WANT TO LOAD SHOULD BE IN THIS PATH

logpath = 'C:/Users/arichards/Documents/Autoloader/log.txt'

winpath = "C:\\Users\\arichards\\Documents\\Autoloader\\Data Files\\GLEntry\\"

savedimport = "https://1085563-sb2.app.netsuite.com/app/setup/assistants/nsimport/importassistant.nl?recid=27&new=T"

unloadedfiles = []

loadedfiles = []

myfiles =  listdir(path)

options = Options()

#options.add_argument("--headless")

options.binary_location = r'C:\Users\arichards\AppData\Local\Mozilla Firefox\firefox.exe'


#driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options) Use this if driver is not automatically found
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

q = 1



#start loop to load all files from selected folder

while i < len(myfiles):

    try:

        driver.get(savedimport)

        time.sleep(5)

        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

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

        WebDriverWait(driver,180).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="next"]')))

        WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.XPATH, '//td[@id="label_fldarr_1"]')))

        time.sleep(.5)



        #enable multithreading

        btn = driver.find_element(By.XPATH, '//td[@id="label_fldarr_1"]')

        btn.click()

        time.sleep(.5)

        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

        #find all checkboxes and select multi threading

        btn = driver.find_elements(By.XPATH, '//img[@class="checkboximage"]')

        btn[5].click()

        time.sleep(.5)

        #queue

        btn = driver.find_element(By.XPATH, '//input[@id="inpt_queuenumber2"]')

        btn.send_keys(str(q))

        if q == 3:

            q = 1

        else:

            q += 1

        

        #go to next page

        btn = driver.find_element(By.XPATH, '//input[@id="next"]')

        btn.click()



        #go to next page

        WebDriverWait(driver,180).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="secondarynext"]'))).click()



        #hover and click run

        #if there is an issue with the file, log it

        #if runs successfully, add success event to log

        try:

            

            btn =  driver.find_element(By.XPATH, '//td[@class="bntBgB multiBnt"]')

            ActionChains(driver).move_to_element(btn).perform()

            time.sleep(1)

            run = driver.find_elements(By.XPATH, '//td[@class="ddmText"]')

            #run.click()

            #if your user created the saved import, set to run[1]. If not, run[0]

            ActionChains(driver).move_to_element(run[0]).click().perform()

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

            print(f'program complete\n{j}/{len(myfiles)} loaded succesfully\n\n')

            driver.quit()

            with open(logpath, 'a') as f:

                f.write(f'\n{j}/{len(myfiles)} loaded succesfully')

        i += 1

        time.sleep(5)

    except NoSuchElementException:

        print('element not found, retrying...')

        continue

    

    except TimeoutException:

        print('timeout, retrying...')

        continue

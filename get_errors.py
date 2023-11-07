from selenium import webdriver
import re
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
#THIS SCRIPT IS INTENDED TO FIND ERROR FILES FOR SEQUENTIALLY NAMED FILES. DUPLICATE NAMED FILES MAY CAUSE ISSUES
#DATE RANGE MAY HAVE TO BE MANUALLY SET BEFORE RUNNING SCRIPT

#figure out logging
#figure out date filter by URL
#figure out only pulling files by naming convention
#figure out sorting files after download

user = '' #case sensitive
url = ''

path = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/Beyond Trust/VMTest/Tran' 
loadelements = []
myfiles =  listdir(path)
options = Options()


driver = webdriver.Firefox(options=options)
driver.get(url)
driver.maximize_window()
cookies = pickle.load(open("cookies.pkl", "rb"))
for cookie in cookies:
    #cookie['domain'] = 
    try:
        driver.add_cookie(cookie)
    except Exception as e:
        print(e)
        pass   

driver.get(url)

tr_elements = driver.find_elements(By.TAG_NAME, "tr")

set = 'no'
for file in myfiles:
    #check every file in load path to see if it matches with loaded files
    for index, tr in enumerate(tr_elements):
        #print(f'Tr Element {index+1}\n{tr.text}\n')
        
        if tr.text.find('CSV Response') != -1 and set == 'no': #set index start point
            first = index
            set = 'yes'
        if tr.text.find('CSV Response') != -1 & tr.text.find(user) != -1 & tr.text.find('Complete') != -1 & tr.text.find(file) != -1 & tr.text.find('Cancelled') == -1:
            final = index - first
            loadelements.append(final)


numloaded = 0
total = 0
for td in loadelements:
    x = driver.find_element(By.XPATH, '//tr[@id="row'+str(td)+'"]')
   
    imported = x.find_element(By.XPATH, '(.//*[@valign="top"])[5]').text 
    pattern = r'(\d+) of (\d+) records imported successfully'
    match = re.search(pattern, imported)

    numloaded = numloaded + int(match.group(1))
    total = total + int(match.group(2))

    if match.group(1) == match.group(2):
        print('100%, will not download CSV Response')
        #do something here where we add to log file
    else:
        #x.find_element(By.XPATH,'.//a').click()
        print('hi')
        #add record count to log file
numunloaded = total - numloaded
print('complete')
print(f'{len(loadelements)} files in the NS job status matched the {len(myfiles)} within the specified directory')
print(f'\n{numloaded} of {total} records loaded')
print(f'\n{numunloaded} errors to handle')
driver.quit()



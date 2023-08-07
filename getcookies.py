from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException, ElementNotInteractableException
import pandas as pd
import time
import pickle


options = Options()
#options.add_argument("--headless")




driver = webdriver.Firefox(options=options)
driver.get("https://1085563-sb1.app.netsuite.com/app/setup/assistants/nsimport/importassistant.nl?recid=20&new=T")
driver.maximize_window()
#time.sleep(60)

btn = driver.find_element(By.XPATH, '//input[@id="email"]')
btn.send_keys('andrew.richards@rsmus.com')
time.sleep(.5)
btn = driver.find_element(By.XPATH, '//input[@id="password"]')
btn.send_keys('Netsuite2023!')

driver.find_element(By.XPATH, '//input[@id="rememberme"]').click()
driver.find_element(By.XPATH, '//button[@id="login-submit"]').click()

time.sleep(3)
driver.find_element(By.XPATH, '//input[@id="uif49"]').send_keys('554138') #ENTER CODE HERE
time.sleep(.5)
driver.find_element(By.XPATH, '//span[@id="uif66"]').click()
time.sleep(.5)
driver.find_element(By.XPATH, '//label[@class="uif427"]').click()
time.sleep(.5)
cookies = driver.get_cookies()

pickle.dump(cookies, open("cookies.pkl", "wb"))

from selenium import webdriver
from pyotp import *
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import pickle


options = Options()
email = ''
password = ''
url = "https://6450923.app.netsuite.com/app/setup/assistants/nsimport/importassistant.nl?recid=144&new=T"
#options.add_argument(r'C:\Users\E075882\AppData\Local\Mozilla\Firefox\Profiles\jlgbg6bx.default-release')

driver = webdriver.Firefox(options=options)
driver.get(url)
driver.maximize_window()


btn = driver.find_element(By.XPATH, '//input[@id="email"]')
btn.send_keys(email)
time.sleep(.5)
btn = driver.find_element(By.XPATH, '//input[@id="password"]')
btn.send_keys(password)

driver.find_element(By.XPATH, '//input[@id="rememberme"]').click()
driver.find_element(By.XPATH, '//button[@id="login-submit"]').click()

time.sleep(3)
token = TOTP('G6SZRWUYA2A5E466C7ME76LDXGHAKJMP')
auth = token.now()
driver.find_element(By.XPATH, '//input[@placeholder="6-digit code"]').send_keys(auth) #ENTER CODE HERE
time.sleep(.5)
driver.find_element(By.XPATH, '//div[@role="button"]').click()
time.sleep(.5)
cookies = driver.get_cookies()

pickle.dump(cookies, open("cookies.pkl", "wb"))
print('completed successfully')
driver.quit()

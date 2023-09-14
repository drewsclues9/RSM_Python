from selenium import webdriver
from pyotp import *
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import pickle


options = Options()
email = 'youremail'
password = 'yourpassword'
url = "yournetsuitedomainurl"

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
token = TOTP('yoursecretkey')
auth = token.now()
driver.find_element(By.XPATH, '//input[@placeholder="6-digit code"]').send_keys(auth) 
time.sleep(.5)
driver.find_element(By.XPATH, '//div[@role="button"]').click()
time.sleep(.5)
cookies = driver.get_cookies()

pickle.dump(cookies, open("cookies.pkl", "wb"))
print('completed successfully')
driver.quit()

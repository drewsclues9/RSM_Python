from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException, ElementNotInteractableException
import pandas as pd
import time

list = pd.read_csv('C:/Users/E075882/OneDrive - RSM/All Data/Client/python/Webscraping/Freight quotes/data.csv')

options = Options()
options.add_argument("--headless")



df = pd.DataFrame(columns = ['id', 'item', 'price'])
i = 0
while i < len(list):
   try:

      driver = webdriver.Firefox(options=options)
      driver.get("https://www.freightquote.com/book/#/single-page-quote")
      driver.maximize_window()
      time.sleep(2)

      WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="Ltl"]'))).click()
      time.sleep(.5)

      if driver.find_element(By.XPATH, '//button[@id="truste-consent-button"]'):
         driver.find_element(By.XPATH, '//button[@id="truste-consent-button"]').click()
      else:
         print("no cookies")
      time.sleep(3)
      
      
      

      
      btn = driver.find_element(By.XPATH, '//input[@class="form-control"]')
      btn.click()
      time.sleep(.5)
      btn.send_keys(Keys.ARROW_DOWN, Keys.ARROW_DOWN, Keys.ENTER)
      time.sleep(.5)
      
      PickupZip = list['PickupZip'].values[i]
      DeliveryZip = list['DeliveryZip'].values[i]


      btn = driver.find_elements(By.XPATH, '//input[@type="text"]')
      btn[0].click()
      time.sleep(.5)
      btn[0].send_keys(Keys.CONTROL, "a")
      time.sleep(.5)
      if len(str(PickupZip)) == 4:
         btn[0].send_keys("0", str(PickupZip))
      else:
         btn[0].send_keys(str(PickupZip)) 
      time.sleep(.5)
      btn[0].send_keys(Keys.ENTER)
      time.sleep(.5)
      
   
     

      btn[1].click()
      time.sleep(.5)
      btn[1].send_keys(Keys.CONTROL, "a")
      time.sleep(.5)
      if len(str(DeliveryZip)) == 4:
         btn[1].send_keys("0", str(DeliveryZip))
      else:
         btn[1].send_keys(str(DeliveryZip))

      
      time.sleep(.5)
      btn[1].send_keys(Keys.ENTER)
      time.sleep(.5)


      #driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
      btn[0].send_keys(Keys.PAGE_DOWN, Keys.PAGE_DOWN)  
   
      btn = driver.find_element(By.XPATH, '//input[@name="items[0].itemDescription"]')
      btn.send_keys(list['ItemDescription'].values[i])
      time.sleep(.5)
      btn = driver.find_element(By.XPATH, '//select[@name="items[0].packageType"]')
      btn.send_keys(list['Packaging'].values[i])
      time.sleep(.5)
      #driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
      time.sleep(.5)
      btn = driver.find_element(By.XPATH, '//input[@name="items[0].height"]')
      btn.clear()
      height = list['Height'].values[i]
      btn.send_keys(str(height))
      time.sleep(.5)
      weight = list['Weight'].values[i]
      btn = driver.find_element(By.XPATH, '//input[@name="items[0].weight"]')
      btn.clear()
      btn.send_keys(str(weight))
      time.sleep(.5)
      btn = driver.find_element(By.XPATH, '//input[@name="items[0].quantity"]')
      btn.clear()
      btn.send_keys(Keys.BACKSPACE)
      quantity = list['Quantity'].values[i]
      btn.send_keys(str(quantity))
      time.sleep(.5)
      btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
      btn.click()
      time.sleep(3)
      
      try:
         WebDriverWait(driver,60).until(EC.visibility_of_element_located((By.XPATH, '//select[@id="sort-select"]'))).click()
         btn = driver.find_element(By.XPATH, '//select[@id="sort-select"]')
         btn.send_keys(list['Sort'].values[i])
         time.sleep(.5)
         btn.click()
         time.sleep(1)
      except:
         txt = driver.find_element(By.XPATH, '//h2[@class="vertical-align-middle justify-center section-header"]')
         if txt.text == "No carriers found":
            print("no carriers found")
            df.loc[i] = [list['RecordID'].values[i], list['ItemDescription'].values[i], 'No carriers found']
            i += 1
            driver.quit()
            continue
         else:
            print("rate limited")
            driver.quit()
            continue

      try:
         prices = driver.find_elements(By.XPATH, '//h4[@class="emphasis bold price-help"]')
         df.loc[i] = [list['RecordID'].values[i], list['ItemDescription'].values[i], prices[0].text]
      except:
         df.loc[i] = [list['RecordID'].values[i], list['ItemDescription'].values[i], 'error']
      print(i)
      i += 1
      driver.quit()
      time.sleep(5)
   except NoSuchElementException:
      print("no such element exception")
      driver.quit()
      time.sleep(30)
      continue
   except UnexpectedAlertPresentException:
      print("unexpected alert")
      driver.quit()
      time.sleep(5)
      continue
   except WebDriverException:
      print("web driver exception")
      driver.quit()
      time.sleep(5)
      continue


   except ElementNotInteractableException:
      print("Element not interactable exception")
      driver.quit()
      time.sleep(5)
      continue

print(df)
df.to_csv('out2.csv')

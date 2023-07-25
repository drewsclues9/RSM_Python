from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time

list = pd.read_csv('C:/Users/E075882/OneDrive - RSM/All Data/Client/python/Webscraping/Freight quotes/FreightInput.csv')

options = Options()
options.add_experimental_option("detach", True)
df = pd.DataFrame(columns = ['item', 'price'])
i = 0
for index,row in list.iterrows():
   try:
      driver = webdriver.Chrome(options=options)

      driver.get("https://www.freightquote.com/")
      driver.maximize_window()
      
      btn = driver.find_element(By.XPATH, '//button[@id="truste-consent-button"]')
      btn.click()
      time.sleep(2)
      date = driver.find_element(By.XPATH, '//input[@id="txtShippingDate"]')
      date.clear()
      date.send_keys(list['LoadingDate'].values[i])
      
      #FIRST PAGE
      PickupZip = list['PickupZip'].values[i]
      origin = driver.find_element(By.XPATH, '//input[@id="txtShippingFrom"]')
      
      if len(str(PickupZip)) == 4:

         origin.send_keys("0", str(PickupZip))
      else:
         origin.send_keys(str(PickupZip)) 

      DeliveryZip = list['DeliveryZip'].values[i]
      destination = driver.find_element(By.XPATH, '//input[@id="txtShippingTo"]')
      if len(str(DeliveryZip)) == 4:
         destination.send_keys("0", str(DeliveryZip))
      else:
         destination.send_keys(str(DeliveryZip)) 

      strtbtn = driver.find_element(By.XPATH, '//button[text()="Start your quote"]')
      strtbtn.click()
      
      #SECOND PAGE
      WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="Ltl"]'))).click()
      #ltl = driver.find_element(By.XPATH, '//input[@id="Ltl"]')
      #ltl.click()

     
      WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH, '//button[@id="btn-next"]'))).click()
      btn = driver.find_element(By.XPATH, '//input[@type="text"]')
      btn.click()
      time.sleep(.5)
      btn.send_keys(Keys.CONTROL, "a")
      time.sleep(.5)
      if len(str(PickupZip)) == 4:

         btn.send_keys("0", str(PickupZip))
      else:
         btn.send_keys(str(PickupZip)) 
      time.sleep(.5)
      btn.send_keys(Keys.ENTER)
      time.sleep(.5)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)
      
         

      #THIRD PAGE
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)

      #FOURTH PAGE
      #do we need any of these?
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)

      #FIFTH PAGE
      btn = driver.find_element(By.XPATH, '//input[@type="text"]')
      btn.click()
      time.sleep(.5)
      btn.send_keys(Keys.CONTROL, "a")
      time.sleep(.5)
      if len(str(DeliveryZip)) == 4:

         btn.send_keys("0", str(DeliveryZip))
      else:
         btn.send_keys(str(DeliveryZip))   
      time.sleep(.5)
      btn.send_keys(Keys.ENTER)
      time.sleep(.5)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)

      #SIXTH PAGE
      driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)
         
   

      #EIGHTH PAGE 
      btn = driver.find_element(By.XPATH, '//input[@name="items[0].itemDescription"]')
      btn.send_keys(list['ItemDescription'].values[i])
      time.sleep(.5)
      btn = driver.find_element(By.XPATH, '//select[@name="items[0].packageType"]')
      btn.send_keys(list['Packaging'].values[i])
      time.sleep(.5)
      driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
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
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)
      #next page
      WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH, '//button[@id="btn-next"]'))).click()
      #btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      #btn.click()
      time.sleep(3)
      #next page
      try:
         WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH, '//select[@id="sort-select"]'))).click()
         btn = driver.find_element(By.XPATH, '//select[@id="sort-select"]')
         btn.send_keys(list['Sort'].values[i])
         time.sleep(.5)
         btn.click()
         time.sleep(1)
      except:
         txt = driver.find_element(By.XPATH, '//h2[@class="vertical-align-middle justify-center section-header"]')
         if txt.text == "No carriers found":
            print("no carriers found")
            df.loc[i] = [list['ItemDescription'].values[i], 'No carriers found']
            i += 1
            continue
         else:
            print("rate limited")
            continue

      try:
         prices = driver.find_elements(By.XPATH, '//h4[@class="emphasis bold price-help"]')
         df.loc[i] = [list['ItemDescription'].values[i], prices[0].text]
      except:
         df.loc[i] = [list['ItemDescription'].values[i], 'error']
      print(i)
      i += 1
   except NoSuchElementException:
      time.sleep(60)
      continue
   #df.to_csv('out2.csv')
   #time.sleep(30)
   #for price in prices:
   #   df.loc[i] = [list['ItemDescription'].values[i], price.text]
   #   i += 1

print(df)
df.to_csv('out2.csv')

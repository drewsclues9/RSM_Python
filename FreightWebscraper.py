from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

list = pd.read_csv('C:/Users/E075882/OneDrive - RSM/All Data/Client/python/Webscraping/Freight quotes/FreightInput.csv')

options = Options()
options.add_experimental_option("detach", True)
df = pd.DataFrame(columns = ['item', 'price'])
i = 0
for index,row in list.iterrows():
   driver = webdriver.Chrome(options=options)

   driver.get("https://www.freightquote.com/")
   driver.maximize_window()
   
   date = driver.find_element(By.XPATH, '//input[@id="txtShippingDate"]')
   date.clear()
   date.send_keys(list['LoadingDate'].values[i])
   
   #FIRST PAGE
   PickupZip = list['PickupZip'].values[i]
   origin = driver.find_element(By.XPATH, '//input[@id="txtShippingFrom"]')
   origin.send_keys(str(PickupZip))

   DeliveryZip = list['DeliveryZip'].values[i]
   destination = driver.find_element(By.XPATH, '//input[@id="txtShippingTo"]')
   destination.send_keys(str(DeliveryZip))

   strtbtn = driver.find_element(By.XPATH, '//button[text()="Start your quote"]')
   strtbtn.click()
   
   #SECOND PAGE
   WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="Ltl"]'))).click()
   #ltl = driver.find_element(By.XPATH, '//input[@id="Ltl"]')
   #ltl.click()

   try:
      WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH, '//button[@id="btn-next"]'))).click()
      #btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      #btn.click()
      time.sleep(3)
   except:
      time.sleep(30)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-back"]')
      btn.click()
      time.sleep(3)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()

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
   #do we need to change requested loading date?
   btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
   btn.click()
   time.sleep(3)

   #SIXTH PAGE
   try:
      btn = driver.find_element(By.XPATH, '//input[@type="text"]')
      #btn.clear()
      #btn.send_keys(str(DeliveryZip))
      btn.send_keys(Keys.ENTER)
      btn = driver.find_element(By.XPATH, '//input[@id="Commercial"]')
      btn.click()
      driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)
   except:
      time.sleep(30)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-back"]')
      btn.click()
      time.sleep(3)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      time.sleep(3)
      driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
      btn = driver.find_element(By.XPATH, '//input[@type="text"]')    
      btn.send_keys(Keys.ENTER)
      btn = driver.find_element(By.XPATH, '//button[@id="btn-next"]')
      btn.click()
      
   #SEVENTH PAGE
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
      print("hi")
      continue

   try:
      prices = driver.find_elements(By.XPATH, '//h4[@class="emphasis bold price-help"]')
      df.loc[i] = [list['ItemDescription'].values[i], prices[0].text]
   except:
      df.loc[i] = [list['ItemDescription'].values[i], 'error']
   print(i)
   i += 1
   #df.to_csv('out2.csv')
   #time.sleep(30)
   #for price in prices:
   #   df.loc[i] = [list['ItemDescription'].values[i], price.text]
   #   i += 1

print(df)
df.to_csv('out2.csv')

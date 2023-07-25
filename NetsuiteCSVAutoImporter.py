from pyautogui import *
import time
import pyautogui as py
import keyboard
from os import listdir

savedimport = 'https://1085563-sb1.app.netsuite.com/app/setup/assistants/nsimport/importassistant.nl?recid=20&new=T'
path = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/Beyond Trust/Data Uploads Test' #ONLY CSV FILES THAT YOU WANT TO LOAD SHOULD BE IN THIS PATH
logpath = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/Beyond Trust/'
winpath = "C:\\Users\\E075882\\OneDrive - RSM\\All Data\\Client\\Beyond Trust\\Data Uploads Test\\"
i = 0
unloadedfiles = []
loadedfiles = []
myfiles = os.listdir(path)
py.moveTo(368, 1367)
py.click()

#start
# TURN ON FOCUS ASSIST/NOTIFICATIONS OFF
while keyboard.is_pressed('q') == False and i < len(myfiles) and i == 0:
    py.keyDown('ctrl')
    py.press('l')
    py.keyUp('ctrl')
    py.write(savedimport)
    py.press('enter')
    time.sleep(5)

    if  py.locateCenterOnScreen("select.png", confidence = 0.5) != None:
        x, y = py.locateCenterOnScreen("select.png", confidence = 0.5)
        py.moveTo(x, y, duration = 1)
        py.leftClick()
        time.sleep(3)
    else:
        continue

    loadfile = myfiles[i] 
    py.write(winpath + loadfile)
    time.sleep(.05)
    py.press('enter')
    time.sleep(3)

    if py.locateCenterOnScreen("notfound.png", confidence = 0.8) != None:
        loadfile = "Not found - " + loadfile
        unloadedfiles.append(loadfile)
        i += 1
        py.press('esc')
        py.press('esc')
        continue

    if py.locateCenterOnScreen("next.png", confidence = 0.8) != None:
        x, y = py.locateCenterOnScreen("next.png", confidence = 0.8)
        py.moveTo(x, y, duration = 1)
        py.leftClick()   
        time.sleep(15) #longer delay to give NS time to "load" file  - INCREASE THIS VALUE FOR PRODUCTION
    else:
        continue

    if py.locateCenterOnScreen("next.png", confidence = 0.8) != None:
        x, y = py.locateCenterOnScreen("next.png", confidence = 0.8)
        py.moveTo(x, y, duration = 1)
        py.leftClick()   
        time.sleep(3) 
    else:
        continue

    if py.locateCenterOnScreen("next.png", confidence = 0.8) != None:
        x, y = py.locateCenterOnScreen("next.png", confidence = 0.8)
        py.moveTo(x, y, duration = 1)
        py.leftClick()   
        time.sleep(3) 
    else:
        continue

    if py.locateCenterOnScreen("run.png", confidence = 0.8) != None:
        x, y = py.locateCenterOnScreen("run.png", confidence = 0.8)
        py.moveTo(x, y, duration = 1)
        py.leftClick()   
        time.sleep(2)
        py.press('enter')
        loadedfiles.append(loadfile)
        time.sleep(3)
    else:
        loadfile = "File import prevented - " + loadfile
        unloadedfiles.append(loadfile)

    i += 1
else:
    print("Loading completed!")
    log = logpath + 'log.txt'
    f = open(log, 'w')
    f.write("Loading completed. \nLoaded files: " + str(loadedfiles) + "|\nUnloaded files: " + str(unloadedfiles))
    f.close()

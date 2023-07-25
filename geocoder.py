import requests
import json
import pandas as pd

df = pd.read_excel('C:/Users/E075882/Downloads/pythoninput.xlsx')

new_df = pd.DataFrame(columns = ['id', 'display name', 'lat', 'lon'])

i = 0
for index,row in df.iterrows():
    try:
        api_url = 'https://geocode.maps.co/search?q='
        val = df['State Zip'].values[i]
        url = api_url +  '{' + str(val) + '}'
        response = requests.get(url)
        json_data = json.loads(response.text)
        new_df.loc[i] = [df['StoreID'].values[i], json_data[0]['display_name'], json_data[0]['lat'], json_data[0]['lon']]
    except:
        new_df.loc[i] = [df['StoreID'].values[i], 'Not Found', 'Not Found', 'Not Found']
    i += 1


new_df.to_excel('C:/Users/E075882/Downloads/pythonoutput2.xlsx')

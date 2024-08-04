import configparser
import requests

config_path = 'config/config.ini'

def generate_config(grocy_url, grocy_port, grocy_api, grocy_default_best_before_days, rapidapi_key):
    grocy_url = grocy_url.rstrip('/')

    response = requests.get(f"{grocy_url}:{grocy_port}/api/objects/quantity_units", headers={
        "accept": "application/json",
        "GROCY-API-KEY": grocy_api
    })
    grocy_default_quantity_unit_id = response.json()[0]['id']

    location_response = requests.get(f"{grocy_url}:{grocy_port}/api/objects/locations", headers={
        "accept": "application/json",
        "GROCY-API-KEY": grocy_api
    })

    grocy_locations = "\n".join([f"{location['name']} = {location['id']}" for location in location_response.json()])

    config = configparser.ConfigParser()
    config['Grocy'] = {
        'GROCY_URL': grocy_url,
        'GROCY_PORT': grocy_port,
        'GROCY_API': grocy_api,
        'GROCY_DEFAULT_QUANTITY_UNIT_ID': grocy_default_quantity_unit_id,
        'GROCY_DEFAULT_BEST_BEFORE_DAYS': grocy_default_best_before_days
    }
    config['GrocyLocation'] = dict(line.split(' = ') for line in grocy_locations.split('\n'))
    config['RapidAPI'] = {'X_RapidAPI_Key': rapidapi_key}

    with open(config_path, 'w') as configfile:
        config.write(configfile)

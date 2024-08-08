import configparser
import requests
import logging

def generate_config(logger, config_path, grocy_url, grocy_port, grocy_api, grocy_default_best_before_days, rapidapi_key):
    try:
        # Remove trailing slash from URL
        grocy_url = grocy_url.rstrip('/')

        # Handle empty grocy_port
        port_part = f":{grocy_port}" if grocy_port else ""

        # Fetch default quantity unit ID
        response = requests.get(f"{grocy_url}{port_part}/api/objects/quantity_units", headers={
            "accept": "application/json",
            "GROCY-API-KEY": grocy_api
        })
        response.raise_for_status()
        grocy_default_quantity_unit_id = response.json()[0]['id']

        # Fetch locations
        location_response = requests.get(f"{grocy_url}{port_part}/api/objects/locations", headers={
            "accept": "application/json",
            "GROCY-API-KEY": grocy_api
        })
        location_response.raise_for_status()
        
        grocy_locations = "\n".join([f"{location['name']} = {location['id']}" for location in location_response.json()])

        # Prepare configuration
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

        # Write configuration to file
        with open(config_path, 'w') as configfile:
            config.write(configfile)

    except requests.RequestException as e:
        if logger:
            logger.error(f"HTTP error occurred: {e}")
        else:
            print(f"HTTP error occurred: {e}")
        raise
    except Exception as e:
        if logger:
            logger.error(f"An unexpected error occurred: {e}")
        else:
            print(f"An unexpected error occurred: {e}")
        raise

def test_generate_config():
    config_path = 'test_config.ini'
    grocy_url = 'http://82.157.206.164'
    grocy_port = 9283
    grocy_api = 'Jo3bCN70KFafEFMlAE9XnkREaRZP8CnS7cYKCpfhWBZlPkPfom'
    grocy_default_best_before_days = 365
    rapidapi_key = 'c8d4c9fdeemsh07e3c4573bb3f16p12b0cejsnb4b979735e7c'

    generate_config(None, config_path, grocy_url, grocy_port, grocy_api, grocy_default_best_before_days, rapidapi_key)

if __name__ == '__main__':
    test_generate_config()
import configparser
import requests
import logging

def generate_config(logger, config_path, grocy_url, grocy_port, grocy_api, grocy_default_best_before_days, rapidapi_key):
    try:
        if not grocy_url.startswith("http://") and not grocy_url.startswith("https://"):
            raise ValueError("grocy_url must be a valid HTTP/HTTPS URL.")
        
        if ":" in grocy_url.split("//")[-1]:
            raise ValueError("grocy_url should not contain a port number.")

        if not isinstance(grocy_port, int) or not (0 < grocy_port < 65536):
            raise ValueError("grocy_port must be a valid port number (1-65535).")

        if not (isinstance(grocy_default_best_before_days, int) and grocy_default_best_before_days > 0):
            raise ValueError("grocy_default_best_before_days must be a positive integer.")

        if not grocy_api:
            raise ValueError("grocy_api cannot be empty.")

        if not rapidapi_key:
            raise ValueError("rapidapi_key cannot be empty.")
            
        grocy_url = grocy_url.rstrip('/')

        response = requests.get(f"{grocy_url}:{grocy_port}/api/objects/quantity_units", headers={
            "accept": "application/json",
            "GROCY-API-KEY": grocy_api
        })
        response.raise_for_status()  # Raise an exception for HTTP errors
        grocy_default_quantity_unit_id = response.json()[0]['id']

        location_response = requests.get(f"{grocy_url}:{grocy_port}/api/objects/locations", headers={
            "accept": "application/json",
            "GROCY-API-KEY": grocy_api
        })
        location_response.raise_for_status()
        
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

    except ValueError as e:
        if logger:
            logger.error(f"Validation error: {e}")
        else:
            print(f"Validation error: {e}")
        raise
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

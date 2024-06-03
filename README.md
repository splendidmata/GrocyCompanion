
# Features

- Barcode recognition, support Chinese prodcuts and world-wide products.
- Grocy product consume with barcode scanning
- Grocy product replenishment with barcode scanning. It can automatically get details of new product and import into Grocy; (product details include: bar code, basic information, pictures, GPC category, shelf-life identification, etc.)

# Quick Start

Config Grocy in the web interface.
- Add API keys for GrocyCompanion: `Settings` - `Manage API keys` - `Add`
- Config your locations: `Manage master Data` - `Locations` - `Add`
- Add GDSInfo attribute to products: `Manage master Data`- `Userfields`- `Add`- Form Information: Entity: products; Name GDSInfo; Title: GDSInfo; Type: Single line text, check “Show this column in table”.
![image (1)](https://github.com/sliveysun/GrocyCompanion/assets/1631565/164ebd98-29a0-4b32-837d-0a2801b5696b)

- Configure Quantity units: `Manage master Data`-`Quantity units` - `Add`

```shell
docker pull osnsyc/grocycompanioncn:latest
```

Cereate config.ini

```ini
# config.ini
[Grocy]
GROCY_URL = http://YOUR_GROCY.COM
GROCY_PORT = 443
GROCY_API = [YOUR_GROCY_API_KEY]
# GROCY_DEFAULT_QUANTITY_UNIT_ID ; Get from this page http://YOUR_GROCY.COM:GROCY_PORT/api/objects/quantity_units 
GROCY_DEFAULT_QUANTITY_UNIT_ID = 1 
GROCY_DEFAULT_BEST_BEFORE_DAYS = 365
# Location ID,与scanner.ino内的位置名称对应
[GrocyLocation] # the locations should be consistant with the locations in Grocy, Get Grocy locations from this page http://YOUR_GROCY.COM:GROCY_PORT/api/objects/locations
pantry = 1
temporary_storage = 2
fridge = 3
living_room = 4
bedroom = 5
bathroom = 6
# Regist RapidAPI account，subscribe to the free plan in https://rapidapi.com/Glavier/api/barcodes1/  copy X_RapidAPI_Key of Endpoints here
[RapidAPI]
X_RapidAPI_Key = YOUR_RapidAPI_API_KEY
```

# Run with Python
1. Configure your python 3.x+ environment.
2. git clone https://github.com/sliveysun/GrocyCompanion.git and cd to GrocyCompanion/
3. Create a virtual environment: python3 -m venv venv
4. Activate the virtual environment: source . /venv/bin/activate
5. Install dependencies pip install -r requirements.txt
6. cp config_example.ini config.ini and edit config.ini to match your situation
7. run server: python app.py
8. view `http://127.0.0.1:9288` in brower, you will get `GrocyCompanion Started!`

# Run with Docker
1. git clone https://github.com/sliveysun/GrocyCompanion.git and cd to GrocyCompanion/
2. mv config_example.ini config.ini and edit config.ini to match your situation
3. docker-compose up -d （server started on port: 9288）
4. view `http://127.0.0.1:9288` in brower, you will get `GrocyCompanion Started!`

GrocyCompanion API test

```shell
curl -X POST -H "Content-Type: application/json" -d '{"client":"temporary_storage","aimid":"]E0","barcode":"8935024140147"}' http://127.0.0.1:9288/add
# replace 8935024140147 with any barcode of your own product 
```
A new product should be added in Grocy

# Acknowledgement

- [https://github.com/tenlee2012/BarCodeQuery](https://github.com/osnsyc/GrocyCompanionCN)

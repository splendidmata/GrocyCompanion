
# Features

- Barcode recognition, support Chinese prodcuts and world-wide products.
- Grocy product consume with barcode scanning
- Grocy product replenishment with barcode scanning. It can automatically get details of new product and import into Grocy; (product details include: bar code, basic information, pictures, GPC category, shelf-life identification, etc.)

# Quick Start

## 0. Config your Grocy
Config Grocy in the web interface.
1. Add API keys for GrocyCompanion: `Settings` - `Manage API keys` - `Add`
2. Config your locations: `Manage master Data` - `Locations` - `Add`
3. Add GDSInfo attribute to products: `Manage master Data`- `Userfields`- `Add`- Form Information: Entity: products; Name GDSInfo; Caption: GDSInfo; Type: Single line text, check “Show this column in table”.

![image (1)](https://github.com/sliveysun/GrocyCompanion/assets/1631565/164ebd98-29a0-4b32-837d-0a2801b5696b)

5. Configure Quantity units: `Manage master Data`-`Quantity units` - `Add`

## 1. Clone project and generate config file
1. deploy your Grocy service  - then you can get your [Grocy Url], [Grocy Port] and [Grocy API key]
2. prepair your [X_RapidAPI_Key] - Register for a RapidAPI account, and subscribe (for free) at https://rapidapi.com/Glavier/api/barcodes1/ under the Pricing section, then you can get X_RapidAPI_Key.
3. git clone https://github.com/sliveysun/GrocyCompanion.git and cd to GrocyCompanion/

## 2. Deploy - 3 choises 
### 2.1 Deploy with Portainer
1. download docker-compose.yml
2. Portainer -> Stacks -> Add stack -> input a name for stack -> select Build method / upload -> upload docker-compose.yml -> Deploy the stack -> Done!

### 2.2 Deploy with Docker
1. cd to GrocyCompanion/
2. docker-compose up -d 

### 2.3 Deploy with Python
1. Configure your python 3.x+ environment.
2. cd to GrocyCompanion/
3. Create a virtual environment: python3 -m venv venv
4. Activate the virtual environment: source . /venv/bin/activate
5. Install dependencies pip install -r requirements.txt
6. run server: python app.py

## 3. Config
view `http://127.0.0.1:9288` (or other suitable address) in browser, then you can config the server and save
![image](https://github.com/user-attachments/assets/73f3e659-38df-4f56-9a50-d50c14bea5de)

## 4. API test
New api - OWL scanner call this api
```shell
curl -X POST -H "Content-Type: application/json" -d '{"device_id":"1234", "device_name":"temporary_storage","aimid":"]E0","barcode":"6941812785041","count":"1"}' http://127.0.0.1:9288/api/update-stock
# replace 6941812785041 with any barcode of your own product
# replace "temporary_storage" with any GrocyLocation in your config.ini
# count = 1 for add, count = -1 for consume
```

Old add api
```shell
curl -X POST -H "Content-Type: application/json" -d '{"device_id":"1234", "device_name":"temporary_storage","aimid":"]E0","barcode":"8935024140147"}' http://127.0.0.1:9288/add
# replace 8935024140147 with any barcode of your own product
# replace "temporary_storage" with any GrocyLocation in your config.ini 
```
A new product should be added in Grocy

Old consume api
```shell
curl -X POST -H "Content-Type: application/json" -d '{"device_id":"1234", "device_name":"temporary_storage","aimid":"]E0","barcode":"8935024140147"}' http://127.0.0.1:9288/consume
# replace 8935024140147 with any barcode of your own product
# replace "temporary_storage" with any GrocyLocation in your config.ini 
```

# Acknowledgement
- [https://github.com/tenlee2012/BarCodeQuery](https://github.com/osnsyc/GrocyCompanionCN)

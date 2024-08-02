
# Features

- Barcode recognition, support Chinese prodcuts and world-wide products.
- Grocy product consume with barcode scanning
- Grocy product replenishment with barcode scanning. It can automatically get details of new product and import into Grocy; (product details include: bar code, basic information, pictures, GPC category, shelf-life identification, etc.)

# Quick Start

## 1. Clone project and generate config file
1. deploy your Grocy service  - then you can get your [Grocy Url], [Grocy Port] and [Grocy API key]
2. prepair your [X_RapidAPI_Key]
3. git clone https://github.com/sliveysun/GrocyCompanion.git and cd to GrocyCompanion/ 
4. run ./generate_config.sh, this interactive shell script will generate config.ini file

## 2. Deploy - 3 choises 
### 2.1 Deploy with Portainer
1. cd to GrocyCompanion/
2. edit volumnes config in docker-compose.yml

chang from:
```yml
volumes:
  - ./config.ini:/usr/src/app/config.ini to
```
to:
```yml
volumes:
  - [ABSOLUTE_PATH_TO]/GrocyCompanion/config.ini:/usr/src/app/config.ini
```
3. download docker-compose.yml to your local
4. Portainer -> Stacks -> Add stack -> input a name for stack -> select Build method / upload -> upload docker-compose.yml -> Deploy the stack -> Done!

### 2.2 Deploy with Docker
1. cd to GrocyCompanion/
2. docker-compose up -d 
3. view `http://127.0.0.1:9288` in brower, you will get `GrocyCompanion Started!`

### 2.3 Deploy with Python
1. Configure your python 3.x+ environment.
2. cd to GrocyCompanion/
3. Create a virtual environment: python3 -m venv venv
4. Activate the virtual environment: source . /venv/bin/activate
5. Install dependencies pip install -r requirements.txt
6. run server: python app.py
7. view `http://127.0.0.1:9288` in brower, you will get `GrocyCompanion Started!`

## 3. API test

```shell
curl -X POST -H "Content-Type: application/json" -d '{"client":"temporary_storage","aimid":"]E0","barcode":"8935024140147"}' http://127.0.0.1:9288/add
# replace 8935024140147 with any barcode of your own product
# replace "temporary_storage" with any GrocyLocation in your config.ini 
```
A new product should be added in Grocy

# Acknowledgement

- [https://github.com/tenlee2012/BarCodeQuery](https://github.com/osnsyc/GrocyCompanionCN)

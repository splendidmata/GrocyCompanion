
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

创建 config.ini 和 docker-compose.yml 文件

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

```yml
# docker-compose.yml
version: "3"
services:
  spider:
    image: osnsyc/grocycompanioncn:latest
    restart: always
    ports:
      - "9288:9288"
    volumes:
      - ./config.ini:/usr/src/app/config.ini
      # - ./u2net.onnx:/root/.u2net/u2net.onnx
    networks:
      - grocy_cn_campanion

networks:
  grocy_cn_campanion:
```

`u2net.onnx`为rembg的模型,程序第一次运行时会自动下载,下载缓慢的也可[手动下载](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx),放入`docker-compose.yml`同目录,并反注释以下一行
```yml
 - ./u2net.onnx:/root/.u2net/u2net.onnx
```
```shell
docker compose up -d
```

打开`http://127.0.0.1:9288`,看到页面显示`GrocyCNCompanion Started!`,服务已成功运行.

GrocyCompanionCN api测试

```shell
curl -X POST -H "Content-Type: application/json" -d '{"client":"temporary_storage","aimid":"]E0","barcode":"8935024140147"}' http://127.0.0.1:9288/add
```

刷新Grocy,出现新物品
| 12     |    螺丝          |     M2x6                                                                                                                                                            |
# 鸣谢

- https://github.com/tenlee2012/BarCodeQuery

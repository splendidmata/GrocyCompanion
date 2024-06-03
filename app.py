#!/bin/env python3
# coding = utf-8
import requests
import json
import configparser
import logging
import os
from pygrocy import Grocy, EntityType
from flask import Flask, request, jsonify, render_template

from returns.result import Result, Success, Failure

from spider.barcode_spider import BarCodeSpider
from spider.barcode_spider import download_img_file

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)                        
                        
config = configparser.ConfigParser()
config.read('config.ini')
GROCY_URL = config.get('Grocy', 'GROCY_URL')
GROCY_PORT = config.getint('Grocy', 'GROCY_PORT')
GROCY_API = config.get('Grocy', 'GROCY_API')
GROCY_DEFAULT_QUANTITY_UNIT_ID = config.getint('Grocy', 'GROCY_DEFAULT_QUANTITY_UNIT_ID')
GROCY_DEFAULT_BEST_BEFORE_DAYS = config.get('Grocy', 'GROCY_DEFAULT_BEST_BEFORE_DAYS')
GROCY_LOCATION = {}
for key in config['GrocyLocation']:
    GROCY_LOCATION[key] = config.get('GrocyLocation', key)
X_RapidAPI_Key = config.get('RapidAPI', 'X_RapidAPI_Key')

app = Flask(__name__)
grocy = Grocy(GROCY_URL, GROCY_API, GROCY_PORT, verify_ssl = True)

def add_generic_product(dict_good, client) -> Result[bool, str]:
    logger.info("dict_good, {}".format(dict_good))
    
    if dict_good is None:
        logger.error("product info is None")
        return Failure("product info is None")
        
    good_name = ""
    if "description" in dict_good:
        good_name = dict_good["description"]
    elif "description_cn" in dict_good:
        good_name = dict_good["description_cn"]
        
    if not good_name:
        logger.error("No good name in the product info")
        return Failure("No good name in the product info")

    best_before_days = GROCY_DEFAULT_BEST_BEFORE_DAYS
    if ("gpc" in dict_good) and dict_good["gpc"]:
        best_before_days = gpc_best_before_days(int(dict_good["gpc"]))
        
    data_grocy = {
        "name": good_name,
        "description": "",
        "location_id": GROCY_LOCATION[client],
        "qu_id_purchase": GROCY_DEFAULT_QUANTITY_UNIT_ID,
        "qu_id_stock": GROCY_DEFAULT_QUANTITY_UNIT_ID,
        "qu_id_consume": GROCY_DEFAULT_QUANTITY_UNIT_ID,
        "qu_id_price": GROCY_DEFAULT_QUANTITY_UNIT_ID,
        "default_best_before_days": best_before_days,
        "default_consume_location_id": GROCY_LOCATION[client],
        "move_on_open": "1",
    }

    # add new product
    logger.debug("data_grocy, {}".format(data_grocy))
    try:
        response_grocy = grocy.add_generic(EntityType.PRODUCTS, data_grocy)
    except Exception as e:
        logger.error("grocy.add_generic got exception - status_code: {} message: {}".format(e.status_code, e.message))
        return Failure("grocy.add_generic got exception - status_code: {} message: {}".format(e.status_code, e.message))
    
    product_id = int(response_grocy["created_object_id"])
    logger.debug("product id is {}".format(product_id))
    
    # add gds info
    logger.debug("--- add gds info ---")
    
    try:
        grocy.set_userfields(
            EntityType.PRODUCTS,
            product_id,
            "GDSInfo",
            json.dumps(dict_good, ensure_ascii=False)
        )
    except Exception as e:
        logger.error("grocy.set_userfields got exception - status_code: {} message: {}".format(e.status_code, e.message))
    
    # add barcode
    logger.debug("--- add barcode ---")
    try:
        # add barcode, ex. 06921168593910
        data_barcode = {
            "product_id": product_id,
            "barcode": dict_good["gtin"]
        }
        
        logger.debug("data_barcode, {}".format(data_barcode))
        grocy.add_generic(EntityType.PRODUCT_BARCODES, data_barcode)
        
        # add barcode, EAN-13, ex. 6921168593910
        if dict_good["gtin"].startswith("0"):
            data_barcode = {
                "product_id": product_id,
                "barcode": dict_good["gtin"].strip("0")
            }
            logger.debug("data_barcode, {}".format(data_barcode))
            grocy.add_generic(EntityType.PRODUCT_BARCODES, data_barcode)   
    except Exception as e:
        logger.error("grocy.add_generic - EntityType.PRODUCT_BARCODES got exception - status_code: {} message: {}".format(e.status_code, e.message))
        
    # add picture
    logger.debug("--- add pic ---")

    pic_url = ""
    if ("picfilename" in dict_good) and dict_good['picfilename']:
        pic_url = dict_good["picfilename"]
    elif ("picture_filename" in dict_good) and dict_good['picture_filename']:
        pic_url = dict_good["picture_filename"]

    if pic_url:
        logger.debug("pic_url:{}".format(pic_url))
        tmp_img_filename = None
        try:
            tmp_img_filename = download_img_file(pic_url)
            if tmp_img_filename:
                grocy.add_product_pic(product_id, tmp_img_filename)
        except Exception as e:
            logger.error("grocy.add_product_pic got exception - status_code: {} message: {}".format(e.status_code, e.message))
        finally:
            if tmp_img_filename:
                os.remove(tmp_img_filename)   
    else:
        logger.error("pic_url is empty")

    logger.debug("--- add_generic_product done ---")
    return Success(True)

def gpc_best_before_days(Code):
    with open('gpc_brick_code.json') as json_file:
        gpc_data = json.load(json_file)

    best_before_days = {}
    best_before_days["7"] = [50370000, 50380000, 50350000,]
    best_before_days["14"] = [50250000, 10000025, 10006970, 10000278, 10006979, ]
    best_before_days["152"] = [50270000, 50310000,]
    best_before_days["305"] = [94000000, 50000000, 10120000, 10110000,]
    best_before_days["670"] = []
    best_before_days["1005"] = [53000000, 47100000, 47190000, 51000000, 10100000,]

    for item in gpc_data["Schema"]:
        if item["Code"] == Code:
            codes = [
                item["Code"],
                item["Code-1"],
                item["Code-2"],
                item["Code-3"]
            ]
            for day, filter_codes in best_before_days.items():
                if any(code in filter_codes for code in codes):
                    return day
                
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/add', methods=['POST'])
def add():
    data = request.json
    client = data.get("client")
    aimid = data.get("aimid")
    barcode = data.get("barcode")

    # parameter verify
    if not client:
        return jsonify({"message": "Missing or empty 'client' parameter"}), 400
    if not aimid:
        return jsonify({"message": "Missing or empty 'aimid' parameter"}), 400
    if not barcode:
        return jsonify({"message": "Missing or empty 'barcode' parameter"}), 400
        
    if aimid != "]E0":
        return jsonify({"message": "Invalid 'aimid' parameter"}), 400
        
    product = None
    try:
        product = grocy.product_by_barcode(barcode)
        logger.info("product_by_barcode return product id: {} name: {}".format(product.id, product.name))
    except Exception as e:
        logger.error("status_code: {} message: {}".format(e.status_code, e.message))
    
    if product is None:
        spider = BarCodeSpider(rapid_api_url="https://barcodes1.p.rapidapi.com/", 
                               x_rapidapi_key=X_RapidAPI_Key,
                               x_rapidapi_host="barcodes1.p.rapidapi.com")
        good = spider.get_good(barcode)
        if isinstance(good, Failure):
            response_data = {"message": "Fail to get good info - {}".format(good.failure()) }
            return jsonify(response_data), 400
            
        good = good.unwrap()
        result = add_generic_product(good, client)
        if isinstance(result, Success):
            response_data = {"message": "New item added successfully"}
            return jsonify(response_data), 200
        else:
            response_data = {"message": "Fail to add new item - {}".format(result.failure())}
            return jsonify(response_data), 400
    
    try:
        grocy.add_product_by_barcode(barcode, 1.0, 0.0)
        response_data = {"message": "Item added successfully"}
        return jsonify(response_data), 200
    except Exception as e:
        logger.error("Fail to add item - status_code: {} message: {}".format(e.status_code, e.message))
        response_data = {"message": "Fail to add item - status_code: {} message: {}".format(e.status_code, e.message)}
        return jsonify(response_data), 400
        

@app.route('/consume', methods=['POST'])
def consume():
    data = request.json
    client = data.get("client")
    aimid = data.get("aimid")
    barcode = data.get("barcode")
    
    logger.info("request data:{}".format(data))
    logger.info("barcode:{}".format(barcode))
    
    # parameter verify
    if not client:
        return jsonify({"message": "Missing or empty 'client' parameter"}), 400
    if not aimid:
        return jsonify({"message": "Missing or empty 'aimid' parameter"}), 400
    if not barcode:
        return jsonify({"message": "Missing or empty 'barcode' parameter"}), 400
        
    if aimid != "]E0":
        return jsonify({"message": "Invalid 'aimid' parameter"}), 400
        
    try:
        grocy.consume_product_by_barcode(barcode)
        response_data = {"message": "Item consume successfully"}
        return jsonify(response_data), 200
    except Exception as e:
        logger.error("Fail to consume item - status_code: {} message: {}".format(e.status_code, e.message))
        response_data = {"message": "Fail to consume item - status_code: {} message: {}".format(e.status_code, e.message)}
        return jsonify(response_data), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9288)

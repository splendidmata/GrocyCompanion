#!/bin/env python3
# coding = utf-8
import requests
import json
import configparser
import logging
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pygrocy import Grocy, EntityType
from returns.result import Result, Success, Failure

from spider.barcode_spider import BarCodeSpider
from spider.barcode_spider import download_img_file
from config_handler import generate_config

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)                        

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 或者使用你自己的强随机字符串

def load_config():
    config = configparser.ConfigParser()
    config_path = os.environ.get('CONFIG_PATH')
    if not config_path:
        raise FileNotFoundError("CONFIG_PATH environment variable not set")
    config.read(config_path)
    return config

def save_config(config):
    config_path = os.environ.get('CONFIG_PATH')
    with open(config_path, 'w') as configfile:
        config.write(configfile)

def update_config():
    global GROCY_URL, GROCY_PORT, GROCY_API, GROCY_DEFAULT_QUANTITY_UNIT_ID, GROCY_DEFAULT_BEST_BEFORE_DAYS, GROCY_LOCATION, X_RapidAPI_Key, grocy
    config = load_config()
    GROCY_URL = config.get('Grocy', 'GROCY_URL')
    GROCY_PORT = config.getint('Grocy', 'GROCY_PORT')
    GROCY_API = config.get('Grocy', 'GROCY_API')
    GROCY_DEFAULT_QUANTITY_UNIT_ID = config.get('Grocy', 'GROCY_DEFAULT_QUANTITY_UNIT_ID')
    GROCY_DEFAULT_BEST_BEFORE_DAYS = config.get('Grocy', 'GROCY_DEFAULT_BEST_BEFORE_DAYS')
    GROCY_LOCATION = {key: config.get('GrocyLocation', key) for key in config['GrocyLocation']}
    X_RapidAPI_Key = config.get('RapidAPI', 'X_RapidAPI_Key')
    grocy = Grocy(GROCY_URL, GROCY_API, GROCY_PORT, verify_ssl=True)

update_config()

def get_error_message(e, base_message):
    status_code = getattr(e, 'status_code', None)
    message = getattr(e, 'message', None)

    if status_code is not None and message is not None:
        full_error_message = base_message + " - status_code: {} message: {}".format(e.status_code, e.message)
    else:
        full_error_message = "Exception occurred: {}".format(str(e))

    return full_error_message

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
        estimated_best_before_days = gpc_best_before_days(int(dict_good["gpc"]))
        if estimated_best_before_days:
            best_before_days = estimated_best_before_days
        
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
        error_message = get_error_message(e, "grocy.add_generic got exception")
        logger.error(error_message)
        return Failure(error_message)
    
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
        error_message = get_error_message(e, "grocy.set_userfields got exception")
        logger.error(error_message)
    
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
                "barcode": dict_good["gtin"].lstrip("0")
            }
            logger.debug("data_barcode, {}".format(data_barcode))
            grocy.add_generic(EntityType.PRODUCT_BARCODES, data_barcode)   
    except Exception as e:
        error_message = get_error_message(e, "grocy.add_generic - EntityType.PRODUCT_BARCODES got exception")
        logger.error(error_message)
        
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
            error_message = get_error_message(e, "grocy.add_product_pic got exception")
            logger.error(error_message)
        finally:
            if tmp_img_filename:
                os.remove(tmp_img_filename)   
    else:
        logger.error("pic_url is empty")

    logger.debug("--- add_generic_product done ---")
    return Success(True)


# gpc code to best_before_days
best_before_days_dict = {
    50370000: 7, 50380000: 7, 50350000: 7,
    50250000: 14, 10000025: 14, 10006970: 14, 10000278: 14, 10006979: 14,
    50270000: 152, 50310000: 152,
    94000000: 305, 50000000: 305, 10120000: 305, 10110000: 305,
    53000000: 1005, 47100000: 1005, 47190000: 1005, 51000000: 1005, 10100000: 1005
}

code_lookup = {}
with open('gpc_brick_code.json') as json_file:
     gpc_data = json.load(json_file)

     for item in gpc_data["Schema"]:
        code = item["Code"]
        codes = [code, item.get("Code-1"), item.get("Code-2"), item.get("Code-3")]
        code_lookup[code] = codes

def gpc_best_before_days(Code):
    if Code in code_lookup:
        for code in code_lookup[Code]:
            if code in best_before_days_dict:
                return str(best_before_days_dict[code])
    return None
                
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        grocy_url = request.form['grocy_url']
        grocy_port = request.form['grocy_port']
        grocy_api = request.form['grocy_api']
        grocy_default_best_before_days = request.form['grocy_default_best_before_days']
        rapidapi_key = request.form['rapidapi_key']
        
        try:
            generate_config(grocy_url, grocy_port, grocy_api, grocy_default_best_before_days, rapidapi_key)
            flash('Configuration updated successfully!', 'success')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        
        return redirect(url_for('index'))
    # GET
    config = load_config()
    config_values = {
        'grocy_url': config.get('Grocy', 'GROCY_URL', fallback=''),
        'grocy_port': config.get('Grocy', 'GROCY_PORT', fallback=''),
        'grocy_api': config.get('Grocy', 'GROCY_API', fallback=''),
        'grocy_default_best_before_days': config.get('Grocy', 'GROCY_DEFAULT_BEST_BEFORE_DAYS', fallback=''),
        'rapidapi_key': config.get('RapidAPI', 'X_RapidAPI_Key', fallback='')
    }
    
    return render_template('index.html', config=config_values)

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
        error_message = get_error_message(e, "grocy.product_by_barcode got exception")
        logger.error(error_message)
    
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
            logger.debug("New item added successfully")
        else:
            response_data = {"message": "Fail to add new item - {}".format(result.failure())}
            return jsonify(response_data), 400
    
    try:
        grocy.add_product_by_barcode(barcode, 1.0, 0.0, get_details = False)
        response_data = {"message": "Item added successfully"}
        return jsonify(response_data), 200
    except Exception as e:
        error_message = get_error_message(e, "Fail to add item")
        logger.error(error_message)
        response_data = {"message": error_message}
        return jsonify(response_data), 400

@app.route('/consume', methods=['POST'])
def consume():
    data = request.data
    logger.info("received raw data: {}".format(data))

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
        error_message = get_error_message(e, "Fail to consume item")
        logger.error(error_message)
        response_data = {"message": error_message}
        return jsonify(response_data), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9288)

#!/bin/env python3
# coding = utf-8
import requests
import logging
import json
import subprocess
import tempfile
import os

from returns.result import Result, Success, Failure

def download_img_file(url):
    try:
        temp_file_path = tempfile.mktemp()
        
        # download to tmp file with wget in silent mode
        subprocess.run(["wget", "-q", "-O", temp_file_path, url], check=True)
        return temp_file_path
    except Exception as e:
        logger.error("download_img_file get exception e {}".format(str(e)))
        return None

class BarCodeSpider:

    def __init__(self, rapid_api_url="https://barcodes1.p.rapidapi.com/", 
                 x_rapidapi_key="", 
                 x_rapidapi_host="barcodes1.p.rapidapi.com"):

        self.logger = logging.getLogger(__name__)

        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        self.base_url = 'https://bff.gds.org.cn/gds/searching-api/ProductService/homepagestatistic'
        self.domestic_url = "https://bff.gds.org.cn/gds/searching-api/ProductService/ProductListByGTIN?PageSize=30&PageIndex=1&SearchItem="
        #self.domestic_url = "https://bff.gds.org.cn/gds/searching-api/ProductService/ProductListByGTIN?PageSize=30&PageIndex=1&Gtin="
        self.domestic_url_simple = "https://bff.gds.org.cn/gds/searching-api/ProductService/ProductSimpleInfoByGTIN?gtin="
        #self.domestic_url_simple = "https://bff.gds.org.cn/gds/searching-api/ProductService/ProductSimpleInfoByGTIN"
        self.imported_url = "https://bff.gds.org.cn/gds/searching-api/ImportProduct/GetImportProductDataForGtin?PageSize=30&PageIndex=1&Gtin="
        self.imported_url_blk = "https://www.barcodelookup.com/"
        self.rapid_api_url = rapid_api_url
        self.x_rapidapi_key = x_rapidapi_key
        self.x_rapidapi_host= x_rapidapi_host

    def download_and_read_file(self, url):
        temp_file_path = tempfile.mktemp()
        try:
            # download to tmp file with wget in silent mode
            subprocess.run(["wget", "-q", "-O", temp_file_path, url], check=True)
            # read file content
            with open(temp_file_path, 'r') as file:
                file_content = file.read()
                return file_content
        except Exception as e:
            self.logger.error("download_and_read_file get exception e {}".format(str(e)))
        finally:
            os.remove(temp_file_path)
        return ""
        
    def fetch_data_from_url(self, url):
        self.logger.debug("fetch_data_from_url, {}".format(url))
        content = self.download_and_read_file(url)
        if content == "":
            self.logger.error("url content is empty, url: {}".format(url))
            return False, ""

        data = json.loads(content)
        if "Code" not in data or data["Code"] != 1:
            self.logger.error("Code is not 1, url: {}".format(url))
            return False, ""
        self.logger.debug("data returned, {}".format(data))
        
        return True, data

    def get_domestic_good(self, barcode) -> Result[dict, str]:
        self.logger.info("--- get_domestic_good ---")
        state, data = self.fetch_data_from_url(self.base_url)
        if state == False:
            self.logger.error("fetch base url failed")
            return Failure("fetch base url failed")
       
        self.logger.debug("-------get basic info----------")
        state, data = self.fetch_data_from_url(self.domestic_url + barcode)
        if state == False:
            self.logger.error("fetch domestic_url with barcode failed, barcode {}".format(barcode))
            return Failure("fetch domestic_url with barcode failed, barcode {}".format(barcode))

        good = data
        if good["Code"] == 2:
            self.logger.error("error, {}, barcode is {}".format(good["Msg"], barcode))
            return Failure("error, {}, barcode is {}".format(good["Msg"], barcode))
        if good["Code"] != 1 or good["Data"]["Items"] == []:
            self.logger.error("error, item no found, barcode is {}".format(barcode))
            return Failure("error, item no found, barcode is {}".format(barcode))

        self.logger.debug("-------get simple info----------")
        base_id = good["Data"]["Items"][0]["base_id"]
        simple_data_url = self.domestic_url_simple + str(barcode) + "&id=" + base_id
        state, simpleInfo = self.fetch_data_from_url(simple_data_url)
        if state:
            good["Data"]["Items"][0]["simple_info"] = simpleInfo["Data"]
        else:
            self.logger.error("error, failed to get item simple info")

        self.logger.debug("good data, {}".format(good["Data"]["Items"][0]))

        return Success(self.rework_good(good["Data"]["Items"][0]))
    
    def get_imported_good(self, barcode) -> Result[dict, str]:
        self.logger.info("--- get_imported_good ---")
        state, data = self.fetch_data_from_url(self.base_url)
        if state:
            state, data = self.fetch_data_from_url(self.imported_url + barcode)
            
        error_message = ""
        if state:
            good = data
            if good["Code"] == 1:
                if (len(good["Data"]["Items"]) == 1):
                    if (good["Data"]["Items"][0]["description_cn"] != None):
                        return Success(self.rework_good(good["Data"]["Items"][0]))
                    else:
                        error_message = "item description_cn is None - "
                elif (len(good["Data"]["Items"]) >= 2):
                    matched_item = good["Data"]["Items"][0]
                    for item in good["Data"]["Items"]:
                        if item["realname"] == item["importer_name"]:
                            matched_item = item
                    return Success(self.rework_good(matched_item))
                else: # 0
                    error_message = "item no found - "
            else:
                if good["Code"] == 2:
                    error_message = "error_message: {} - ".format(good["Msg"])
        
        self.logger.error(error_message + "barcode: {}, fetched data : {}".format(barcode, data))
        return self.get_imorted_good_from_blk(barcode)            

    def parse_good_info(self, good_dict, barcode) -> Result[dict, str]:
        good = {}
        try:
            good["description_cn"] = good_dict["product"]["title"]
            good["picfilename"] = good_dict["product"]["images"][0]
            attributes = good_dict["product"]["attributes"]
            good["specification_cn"] = ", ".join([f"{key}:{value}" for key, value in attributes.items()])
            good["gtin"] = barcode
        except Exception as e:
            self.logger.error("rapid api data format error, error_message:{}".format(str(e)))
            return Failure("rapid api data format error, error_message:{}".format(str(e)))
        
        self.logger.info("good info, {}".format(good))
        return Success(good)
        
    def get_imorted_good_from_blk(self, barcode) -> Result[dict, str]:
        self.logger.info("--- get_imorted_good_from_blk ---")
        
        querystring = {"query": barcode}
        headers = {
            "X-RapidAPI-Key": self.x_rapidapi_key,
            "X-RapidAPI-Host": self.x_rapidapi_host
        }
        try:
            response = requests.get(self.rapid_api_url, headers=headers, params=querystring)
            good_dict = response.json()
        except:
            self.logger.error("request rapid api got error")
            return Failure("request rapid api got error")
        
        if good_dict is None:
            self.logger.error("response data from rapid api is None")
            return Failure("response data from rapid api is None")
        
        if "product" not in good_dict:
            self.logger.error("'product' is not in good_dict, {}".format(good_dict))
            self.logger.error("{} is not a valid barcode number".format(barcode))
            return Failure("{} is not a valid barcode number".format(barcode))
        
        return self.parse_good_info(good_dict, barcode)
    
    def rework_good(self, good):
        if "id" in good:
            del good["id"]
        if "f_id" in good:
            del good["f_id"]
        if "brandid" in good:
            del good["brandid"]
        if "base_id" in good:
            del good["base_id"]

        if good["branch_code"]:
            good["branch_code"] = good["branch_code"].strip()
        if "picture_filename" in good:
            if good["picture_filename"] and (not good["picture_filename"].startswith("http")):
                good["picture_filename"] = "https://oss.gds.org.cn" + good["picture_filename"]
        if "picfilename" in good:
            if good["picfilename"] and (not good["picfilename"].startswith("http")):
                good["picfilename"] = "https://oss.gds.org.cn" + good["picfilename"]

        return good

    def get_good(self, barcode) -> Result[dict, str]:
        if barcode.startswith("69") or barcode.startswith("069"):
            return self.get_domestic_good(barcode)
        else:
            return self.get_imported_good(barcode)
        
def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    spider = BarCodeSpider(rapid_api_url="https://barcodes1.p.rapidapi.com/", 
                           x_rapidapi_key='-',
                           x_rapidapi_host="barcodes1.p.rapidapi.com")
    # International commodity
    #good = spider.get_good('3346476426843')
    good = spider.get_good('024300041044')
    print("International commodity")
    print(good)
 
'''
    # Chinese commodity
    good = spider.get_good('06917878036526')
    print("Chinese commodity")
    print(good)
    
    # Imported commodity
    good = spider.get_good('4901201103803')
    print("Imported commodity")
    print(good)
'''

if __name__ == '__main__':
    main()

'''
国产商品字典
"keyword": "农夫山泉",
"branch_code": "3301    ",
"gtin": "06921168593910",
"specification": "900毫升",
"is_private": false,
"firm_name": "农夫山泉股份有限公司",
"brandcn": "农夫山泉",
"picture_filename": "https://oss.gds.org.cn/userfile/uploada/gra/1712072230/06921168593910/06921168593910.1.jpg",
"description": "农夫山泉NFC橙汁900ml",
"logout_flag": "0",
"have_ms_product": 0,
"base_create_time": "2018-07-10T10:01:31.763Z",
"branch_name": "浙江分中心",
"base_source": "Source",
"gpc": "10000201",
"gpcname": "即饮型调味饮料",
"saledate": "2017-11-30T16:00:00Z",
"saledateyear": 2017,
"base_last_updated": "2019-01-09T02:00:00Z",
"base_user_id": "源数据服务",
"code": "69211685",
"levels": null,
"levels_source": null,
"valid_date": "2023-02-16T16:00:00Z",
"logout_date": null,
"gtinstatus": 1
'''

'''
进口商品字典
"gtin": "04901201103803",
"description_cn": "UCC117速溶综合咖啡90g",
"specification_cn": "90克",
"brand_cn": "悠诗诗",
"gpc": "10000115",
"gpc_name": "速溶咖啡",
"origin_cn": "392",
"origin_name": "日本",
"codeNet": null,
"codeNetContent": null,
"suggested_retail_price": 0,
"suggested_retail_price_unit": "人民币",
"txtKeyword": null,
"picfilename": "https://oss.gds.org.cn/userfile/importcpfile/201911301903478446204015916.png",
"realname": "磨禾（厦门）进出口有限公司",
"branch_code": "3501",
"branch_name": "福建分中心",
"importer_name": "磨禾（厦门）进出口有限公司",
"certificatefilename": null,
"certificatestatus": 0,
"isprivary": 0,
"isconfidentiality": 0,
"datasource": 0
'''

'''
国际商品字典
'''

#!/bin/bash

# 获取用户输入
read -p "请输入 Grocy URL (例如 http://42.194.226.215): " grocy_url
read -p "请输入 Grocy 端口: " grocy_port
read -p "请输入 Grocy API 密钥: " grocy_api
read -p "请输入默认保质期天数 (例如 365): " grocy_default_best_before_days

read -p "请输入 RapidAPI 密钥: " rapidapi_key

# 去掉 Grocy URL 末尾的 '/'
grocy_url=${grocy_url%/}

# 获取 GROCY_DEFAULT_QUANTITY_UNIT_ID
response=$(curl -s -X 'GET' "${grocy_url}:${grocy_port}/api/objects/quantity_units" \
-H "accept: application/json" \
-H "GROCY-API-KEY:${grocy_api}")

# 调试输出：打印获取的数量单位响应
echo "数量单位响应: $response"

# 从响应中提取第一个 ID
grocy_default_quantity_unit_id=$(echo "$response" | grep -o '"id":[0-9]*' | head -n 1 | grep -o '[0-9]*')

# 调试输出：打印提取的数量单位 ID
echo "提取的数量单位 ID: $grocy_default_quantity_unit_id"

# 拼出并打印 curl 命令
location_curl_cmd="curl -s -X 'GET' '${grocy_url}:${grocy_port}/api/objects/locations' -H 'accept: application/json' -H 'GROCY-API-KEY:${grocy_api}'"
echo "执行的 curl 命令: $location_curl_cmd"

# 执行 curl 命令获取 GrocyLocation 信息
location_response=$(eval $location_curl_cmd)

# 调试输出：打印获取的位置响应
echo "位置响应: $location_response"

# 检查是否获取到位置响应
if [ -z "$location_response" ]; then
    echo "错误：未能获取到位置响应。请检查URL、端口和API密钥是否正确。"
    exit 1
fi

# 解析 GrocyLocation 信息
grocy_locations=$(echo "$location_response" | grep -oE '"id":[0-9]+,"name":"[^"]+"' | sed -E 's/"id":([0-9]+),"name":"([^"]+)"/\2 = \1/')

# 调试输出：打印解析的位置信息
echo "解析的位置信息: $grocy_locations"

# 生成 config.ini 文件
cat <<EOL > config.ini
[Grocy]
GROCY_URL = ${grocy_url}
GROCY_PORT = ${grocy_port}
GROCY_API = ${grocy_api}
GROCY_DEFAULT_QUANTITY_UNIT_ID = ${grocy_default_quantity_unit_id}
GROCY_DEFAULT_BEST_BEFORE_DAYS = ${grocy_default_best_before_days}

[GrocyLocation]
${grocy_locations}

[RapidAPI]
X_RapidAPI_Key = ${rapidapi_key}
EOL

echo "配置文件 config.ini 生成成功!"


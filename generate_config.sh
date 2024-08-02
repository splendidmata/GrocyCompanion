#!/bin/bash

# Get user input
read -p "Please enter the Grocy URL: " grocy_url
read -p "Please enter the Grocy port: " grocy_port
read -p "Please enter the Grocy API key: " grocy_api
read -p "Please enter the default best before days (e.g., 365): " grocy_default_best_before_days
read -p "Please enter the RapidAPI key: " rapidapi_key

# Remove trailing '/' from Grocy URL
grocy_url=${grocy_url%/}

# Get GROCY_DEFAULT_QUANTITY_UNIT_ID
response=$(curl -s -X 'GET' "${grocy_url}:${grocy_port}/api/objects/quantity_units" \
-H "accept: application/json" \
-H "GROCY-API-KEY:${grocy_api}")

# Debug output: Print the quantity units response
echo "Quantity units response: $response"

# Extract the first ID from the response
grocy_default_quantity_unit_id=$(echo "$response" | grep -o '"id":[0-9]*' | head -n 1 | grep -o '[0-9]*')

# Debug output: Print the extracted quantity unit ID
echo "Extracted quantity unit ID: $grocy_default_quantity_unit_id"

# Construct and print the curl command
location_curl_cmd="curl -s -X 'GET' '${grocy_url}:${grocy_port}/api/objects/locations' -H 'accept: application/json' -H 'GROCY-API-KEY:${grocy_api}'"
echo "Executing curl command: $location_curl_cmd"

# Execute the curl command to get GrocyLocation information
location_response=$(eval $location_curl_cmd)

# Debug output: Print the location response
echo "Location response: $location_response"

# Check if the location response is empty
if [ -z "$location_response" ]; then
    echo "Error: Failed to get location response. Please check the URL, port, and API key."
    exit 1
fi

# Use Python to decode Unicode escape characters and parse JSON
grocy_locations=$(echo "$location_response" | python3 -c '
import sys
import json

data = json.loads(sys.stdin.read())
for location in data:
    name = location["name"]
    id = location["id"]
    print(f"{name} = {id}")
')

# Debug output: Print the parsed location information
echo "Parsed location information: $grocy_locations"

# Check if the parsed location information is empty
if [ -z "$grocy_locations" ]; then
    echo "Error: Failed to parse location information. Please check the API response."
    exit 1
fi

# Generate the config.ini file
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

echo "Configuration file config.ini generated successfully!"


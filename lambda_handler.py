import requests
import json
import os
import math
from dotenv import load_dotenv
from gold_weights import gold_weights

load_dotenv()

GOLD_API_KEY = os.getenv('GOLD_API_KEY')

# Shopify API credentials and store details
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_PASSWORD = os.getenv('SHOPIFY_API_PASSWORD')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
SHOPIFY_PRODUCT_IDS = ['7875388244118', '7919937454230']  # Example: ['1234567890', '0987654321']


def get_current_gold_price():
    api_key = GOLD_API_KEY
    symbol = "XAU"
    curr = "USD"
    url = f"https://www.goldapi.io/api/{symbol}/{curr}"

    headers = {
        "x-access-token": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        gold_data = response.json()
        return gold_data
    except requests.exceptions.RequestException as e:
        print("Error in fetching gold price:", str(e))
        return None


def calculate_price_per_variant(gold_price, karat, thickness, length):
    extra_per_gram = 11.40
    cost_per_gram = 1.40

    if karat == '14K':
        price_per_gram = gold_price['price_gram_14k']
    elif karat == '10K':
        price_per_gram = gold_price['price_gram_10k']
    else:
        raise ValueError("Invalid karat value")

    weight = gold_weights[karat][thickness][length]
    new_price = (price_per_gram + extra_per_gram) * weight
    cost = (price_per_gram + cost_per_gram) * weight
    new_price = math.ceil(new_price) if new_price - int(new_price) > 0 else int(new_price)

    return new_price, cost, weight


def update_shopify_product_prices(product_id, gold_price_data):
    shopify_url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2022-01/products/{product_id}.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_API_PASSWORD
    }

    try:
        response = requests.get(shopify_url, headers=headers)
        print(response)
        response.raise_for_status()
        product_data = response.json()

        for variant in product_data['product']['variants']:
            title_parts = variant['title'].split(' / ')
            if len(title_parts) < 3:
                print(f"Warning: Skipping variant with unexpected title format: {variant['title']}")
                continue

            karat = title_parts[0]
            length = int(title_parts[1][:-1])
            thickness = title_parts[2]

            new_price, cost, weight = calculate_price_per_variant(gold_price_data, karat, thickness, length)

            # Construct the payload for updating the variant
            payload = {
                "variant": {
                    "id": variant['id'],
                    "price": str(new_price),
                    "cost": str(cost),
                    "grams": weight,
                    "inventory_management": None,
                    "weight_unit": "g"
                }
            }

            variant_update_url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2022-01/variants/{variant['id']}.json"
            update_response = requests.put(variant_update_url, headers=headers, data=json.dumps(payload))
            update_response.raise_for_status()

        print(f"Prices and costs for all variants of product {product_id} updated successfully.")
    except requests.exceptions.RequestException as e:
        print("Error in updating Shopify product prices:", str(e))


def lambda_handler():
    gold_price_data = get_current_gold_price()
    if gold_price_data:
        for product_id in SHOPIFY_PRODUCT_IDS:
            update_shopify_product_prices(product_id, gold_price_data)


if __name__ == '__main__':
    lambda_handler()

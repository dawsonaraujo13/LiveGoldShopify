import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

GOLD_API_KEY = 'your_gold_api_key'

# Shopify API credentials and store details
SHOPIFY_API_KEY = 'your_shopify_api_key'
SHOPIFY_API_PASSWORD = 'your_shopify_api_password'
SHOPIFY_STORE_NAME = 'your_shopify_store_name'
SHOPIFY_PRODUCT_IDS = ['your_14k_gold_product_id', 'your_10k_gold_product_id']  # Example: ['1234567890', '0987654321']


# Function to fetch the current gold price
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


# Function to calculate new product price based on weight
def calculate_price_per_variant(gold_price, karat, weight):
    extra_per_gram = 1.40
    flat_fee = 10.00

    if karat == '14k':
        price_per_gram = gold_price['price_gram_14k']
    elif karat == '10k':
        price_per_gram = gold_price['price_gram_10k']
    else:
        raise ValueError("Invalid karat value")

    new_price = (price_per_gram + extra_per_gram) * weight
    new_price += flat_fee
    return new_price


# Function to update product price on Shopify for all variants
def update_shopify_product_prices(product_id, gold_price_data):
    shopify_url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2022-01/products/{product_id}.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_API_PASSWORD
    }

    try:
        response = requests.get(shopify_url, headers=headers)
        response.raise_for_status()
        product_data = response.json()
        variants = product_data['product']['variants']

        for variant in variants:
            # Assuming the variant title includes the karat and weight information
            # Example variant title: "Necklace - 14k - 5g"
            title_parts = variant['title'].split(' - ')
            karat = title_parts[1]
            weight = float(title_parts[2].replace('g', ''))  # Extract weight and convert to float

            new_price = calculate_price_per_variant(gold_price_data, karat, weight)
            variant['price'] = str(new_price)

        update_response = requests.put(shopify_url, headers=headers, data=json.dumps(product_data))
        update_response.raise_for_status()
        print(f"Prices for all variants of product {product_id} updated successfully.")
    except requests.exceptions.RequestException as e:
        print("Error in updating Shopify product prices:", str(e))


def main():
    gold_price_data = get_current_gold_price()
    if gold_price_data:
        for product_id in SHOPIFY_PRODUCT_IDS:
            update_shopify_product_prices(product_id, gold_price_data)


if __name__ == "__main__":
    main()

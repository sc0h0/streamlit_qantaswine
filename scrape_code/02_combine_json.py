import json
import os

# Step 1: Get all of the json_dump_page_{page_number}.json files from the 'temp' folder
json_folder = 'temp'
json_files = [f for f in os.listdir(json_folder) if f.startswith('json_dump_page_') and f.endswith('.json')]
print(json_files)

# Step 2: Iterate through all JSON files and extract the products array, then save it as products_data.json
products = []
for json_file in json_files:
    file_path = os.path.join(json_folder, json_file)
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
        # Check if the data is a dictionary and contains the necessary structure
        if isinstance(data, dict):
            try:
                # Extract products if the key exists
                product_list = data['props']['pageProps'].get('productSearchResults', {}).get('products', [])
                if product_list:
                    products.extend(product_list)
                else:
                    print(f"No products found in {json_file}.")
            except KeyError as e:
                print(f"Error: {e} key not found in the JSON structure of {json_file}.")
        else:
            print(f"Unexpected data type in {json_file}. Expected a dictionary.")


# Save the products to a new file or print them
if products:
    # Save the products array to a new JSON file
    with open(os.path.join(json_folder, 'products_extracted.json'), 'w', encoding='utf-8') as output_file:
        json.dump(products, output_file, indent=4)

else:
    print("No products found in the JSON file.")

import json
import csv

# Load the products data from the JSON file
with open('temp/products_extracted.json', 'r', encoding='utf-8') as file:
    products_data = json.load(file)

# Define CSV file headers, including five columns for case variants
fieldnames = [
    'name', 
    'key', 
    'slug', 
    'casevariant_1', 
    'casevariant_2', 
    'casevariant_3', 
    'casevariant_4', 
    'casevariant_5', 
    'currentprice_cashprice', 
    'currentprice_bonusPoint', 
    'validfrom', 
    'validto'
]

# Open a CSV file for writing
with open('temp/products_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    # Write the header
    writer.writeheader()
    
    # Loop through each product and extract relevant information
    for product in products_data:
        # Extract relevant information from each product
        extracted_info = {
            "name": product.get("name", None),
            "key": product.get("key", None),
            "slug": product.get("slug", None),
            "casevariant_1": None,
            "casevariant_2": None,
            "casevariant_3": None,
            "casevariant_4": None,
            "casevariant_5": None,
            "currentprice_cashprice": None,
            "currentprice_bonusPoint": None,
            "validfrom": None,
            "validto": None
        }

        # Extract information from the 'variants' list if it exists
        variants = product.get("variants", [])
        if variants:
            variant = variants[0]  # Assuming we're interested in the first variant

            # Extract case variants (up to 5) if they exist, otherwise use displayQuantity
            case_variants = variant.get("allAttributes", {}).get("caseVariants", [])
            if case_variants:
                for i, case_variant in enumerate(case_variants[:5]):
                    extracted_info[f"casevariant_{i+1}"] = case_variant.get("key", None)
            else:
                # Fallback to 'displayQuantity' if no 'caseVariants' are found
                extracted_info["casevariant_1"] = variant.get("allAttributes", {}).get("displayQuantity", None)

            # Extract pricing information (if it exists)
            current_price = variant.get("currentPrice", {})
            extracted_info["currentprice_cashprice"] = current_price.get("cashPrice", {}).get("amount", None)
            extracted_info["currentprice_bonusPoint"] = current_price.get("bonusPoint", None)
            extracted_info["validfrom"] = current_price.get("validFrom", None)
            extracted_info["validto"] = current_price.get("validUntil", None)

        # Write the extracted data as a row in the CSV file
        writer.writerow(extracted_info)

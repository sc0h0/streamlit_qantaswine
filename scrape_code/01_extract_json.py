import json
import os
from playwright.sync_api import sync_playwright

# Create a 'temp' directory in the same location as the Python script if it doesn't exist
os.makedirs('temp', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Launch browser in non-headless mode
    page = browser.new_page()

    # Navigate to the specific page with BonusPoints filter
    page.goto('https://wine.qantas.com/c/browse-products?BonusPoints=1')
    
    # Extract the number of pages by locating the 'page-last' link
    last_page_link = page.locator('a[data-testid="page-last"]').get_attribute('href')

    # Extract the page number from the 'href' attribute
    if last_page_link:
        last_page_number = last_page_link.split('-')[-1]  # Assumes the page number is at the end of the URL
        print(f"Total number of pages: {last_page_number}")
    else:
        print("Could not find the last page link.")
        
    # Convert the last page number to an integer
    last_page_number = int(last_page_number)
    
    # For each page, extract the JSON data and save it to a file as json_dump_page_{page_number}.json
    # We're already on the first, so we don't need to navigate to it
    for page_number in range(1, last_page_number + 1):
        
        if page_number > 1:
            # Navigate to the next page e.g. https://wine.qantas.com/c/browse-products/page-2?BonusPoints=1&sort=featured
            page.goto(f'https://wine.qantas.com/c/browse-products/page-{page_number}?BonusPoints=1&sort=featured')

        # Extract JSON data from the script tag with id '__NEXT_DATA__'
        script_content = page.locator("script#__NEXT_DATA__").evaluate("el => el.textContent")

        # Load the JSON content into a Python dictionary
        json_data = json.loads(script_content)

        # Save the JSON to a file inside the 'temp' folder
        with open(os.path.join('temp', f'json_dump_page_{page_number}.json'), 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, indent=4)

    # Ensure that the Playwright browser is closed
    page.close()
    browser.close()

import os
import shutil
from datetime import datetime

# Step 1: Generate a timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Step 2: Get the current directory where the script is located
current_directory = os.path.dirname(os.path.abspath(__file__))

# Step 3: Define directories relative to the current directory
temp_folder = os.path.join(current_directory, 'temp')
archive_dump_folder = os.path.join(current_directory, 'archive/dump')
archive_combined_folder = os.path.join(current_directory, 'archive/combined')
archive_csv_folder = os.path.join(current_directory, 'archive/csv')

# Step 4: Ensure archive directories exist
os.makedirs(archive_dump_folder, exist_ok=True)
os.makedirs(archive_combined_folder, exist_ok=True)
os.makedirs(archive_csv_folder, exist_ok=True)

# Step 5: Move and rename JSON dump files
json_dump_files = [f for f in os.listdir(temp_folder) if f.startswith('json_dump_page_') and f.endswith('.json')]

for json_file in json_dump_files:
    old_path = os.path.join(temp_folder, json_file)
    new_filename = f'{timestamp}_{json_file}'
    new_path = os.path.join(archive_dump_folder, new_filename)
    shutil.move(old_path, new_path)
    print(f"Moved {json_file} to {new_path}")

# Step 6: Move and rename products_extracted.json
extracted_file = 'products_extracted.json'
old_extracted_path = os.path.join(temp_folder, extracted_file)
if os.path.exists(old_extracted_path):
    new_extracted_filename = f'{timestamp}_{extracted_file}'
    new_extracted_path = os.path.join(archive_combined_folder, new_extracted_filename)
    shutil.move(old_extracted_path, new_extracted_path)
    print(f"Moved {extracted_file} to {new_extracted_path}")
else:
    print(f"{extracted_file} not found in {temp_folder}")

# Step 7: Move and rename products_data.csv
csv_file = 'products_data.csv'
old_csv_path = os.path.join(temp_folder, csv_file)
if os.path.exists(old_csv_path):
    new_csv_filename = f'{timestamp}_{csv_file}'
    new_csv_path = os.path.join(archive_csv_folder, new_csv_filename)
    shutil.move(old_csv_path, new_csv_path)
    print(f"Moved {csv_file} to {new_csv_path}")
else:
    print(f"{csv_file} not found in {temp_folder}")

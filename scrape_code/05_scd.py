import pandas as pd
import os
from datetime import datetime
import pandasql as psql
import hashlib
from tabulate import tabulate

checksum_columns = [
    'wine_name', 'slug', 'casevariant_1', 'casevariant_2', 'casevariant_3',
    'casevariant_4', 'casevariant_5', 'currentprice_cashprice', 
    'currentprice_bonusPoint', 'validfrom', 'validto'
]

# Step 1: Load CSV files
path = 'archive/csv'
all_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.csv')]

dataframes = []
for file in all_files:
    # Extract the date and time from the filename, e.g., '20240818_152850'
    timestamp_str = os.path.basename(file).split('_')[0] + os.path.basename(file).split('_')[1]
    snapshot_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')  # Convert string to datetime
    
    df = pd.read_csv(file)
    df['snapshot_time'] = snapshot_time  # Add the snapshot_time column to the DataFrame
    dataframes.append(df)

# Combine all dataframes
df_combined = pd.concat(dataframes)

# rename columns name and key to wine_name and wine_key
df_combined = df_combined.rename(columns={'name': 'wine_name', 'key': 'wine_key'})

"""
# print the table in ascii form using tabulate library

print(tabulate(df_combined.head(), headers='keys', tablefmt='psql'))

# print schema of df_combined
print(df_combined.dtypes)
"""

# select only one record per key based on the latest snapshot_time
df_01 = psql.sqldf("""
--sql
select
b.*,
row_number() over (partition by wine_key, snapshot_date order by snapshot_time desc) as rn_01
from
(
    select
    a.*,
    substr(snapshot_time, 1, 10) as snapshot_date
    from 
    df_combined a
) b 
order by wine_key, snapshot_time desc
--endsql
""")
# print schema of df_01
#print(df_01.dtypes)
#print(tabulate(df_01.head(), headers='keys', tablefmt='psql'))

df_02 = psql.sqldf("""
--sql
select 
*
from df_01
where rn_01 = 1
--endsql
""")
    

# Create checksums to detect changes based on the specified changing columns
df_02['record_checksum'] = df_02.apply(
    lambda row: hashlib.md5(
        ''.join([str(row[col]) for col in checksum_columns]).encode()
    ).hexdigest(), 
    axis=1
)

columns_str_df_02 = ', '.join(checksum_columns)

# SQL query using the dynamically constructed column string
df_02_distinct = psql.sqldf(f"""
--sql
select distinct
record_checksum,
{columns_str_df_02}
from
df_02
--endsql
""")

# get the min and max snapshot_date for each wine_key and checksum
df_03 = psql.sqldf("""
--sql
select
wine_key,
record_checksum,
min(snapshot_date) as eff_from,
max(snapshot_date) as eff_to
from df_02
group by
wine_key,
record_checksum
order by wine_key, eff_from
--endsql
""")

# print any records with multitple counts group by wine_key. use python code
#psql.sqldf("""select wine_key, count(*) from df_03 group by wine_key having count(*) > 1""")

# get all of the unique keys across all snapshots
df_04 = psql.sqldf("""
--sql
select
distinct
wine_key
from 
df_03
--endsql
""")

# get the global lastest eff_to
df_05 = psql.sqldf("""
--sql
select
max(eff_to) as global_max_eff_to
from df_03
--endsql
""")

# get the max_eff_to of each key
df_06 = psql.sqldf("""
--sql
select
wine_key,
max(eff_to) as max_eff_to
from df_03  
group by
wine_key
--endsql
""")

# flag which records are deleted
df_07 = psql.sqldf("""
--sql
select
a.wine_key,
a.max_eff_to,
b.global_max_eff_to,

case
when a.max_eff_to = b.global_max_eff_to then 0
else 1
end as rec_deleted_flag

from
df_06 a
cross join df_05 b    
--endsql
""")       


# now combine tables
df_08 = psql.sqldf("""
--sql
select
a.wine_key,
a.record_checksum,
a.eff_from,
a.eff_to as eff_to_original,

b.max_eff_to,

case
when a.eff_to = b.max_eff_to then '9999-12-31'
else a.eff_to
end as eff_to,

case
when a.eff_to = b.max_eff_to and c.rec_deleted_flag = 1 then 1
else 0
end as rec_deleted_flag

-- this is wine_key, checksum, eff_from, eff_to, max_eff_to table
from df_03 a
-- left join on max_eff_to of wine_key
left join df_06 b on a.wine_key = b.wine_key
-- left join on which records are deleted
left join df_07 c on a.wine_key = c.wine_key
order by a.wine_key, a.eff_from desc
--endsql
""")

# Convert the list of columns to a comma-separated string with table alias `b`
df_09_columns_str = ', '.join([f'b.{col}' for col in checksum_columns])

# join back the original data from df_02. only select the check_sum_columns
df_09 = psql.sqldf(f"""
--sql
select
a.wine_key,
a.eff_from,
a.eff_to,
a.rec_deleted_flag,
a.record_checksum,
{df_09_columns_str}
from
df_08 a
left join df_02_distinct b on b.record_checksum = a.record_checksum
--endsql
""")

# write scd file to /sdc folder
df_09.to_csv('scd/qantas_bonuspoints_true.csv', index=False)


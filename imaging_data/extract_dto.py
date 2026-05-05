from urllib.parse import urlparse
import pyarrow
import pyarrow.fs
import pandas as pd
import pyarrow.compute as pc
import pyarrow.dataset as ds
import datetime

occurrence_data = "https://s3.waw3-1.cloudferro.com/emodnet/emodnet_biology/12639/marine_biodiversity_observations_2026-02-26.parquet"

# Define filter parameters
target_dates = ["2021-07", "2021-08", "2021-10", "2021-12"]
# Bounding box: lat 51.4-51.5, lon 2.75-2.9
min_lat, max_lat = 51.4, 51.5
min_lon, max_lon = 2.75, 2.9

parsed_url = urlparse(occurrence_data)
host = parsed_url.hostname
bucket_name = parsed_url.path.split('/')[1]
key = '/'.join(parsed_url.path.split('/')[2:])
print("host =", host)
print("bucket_name =", bucket_name)
print("key =", key)

s3 = pyarrow.fs.S3FileSystem(endpoint_override=host, anonymous=True)
s3_path = f"{bucket_name}/{key}"

dataset = ds.dataset(s3_path, filesystem=s3, format="parquet")
print(dataset.schema)

columns_needed = ["aphiaid", "latitude", "longitude", "parameter", "parameter_value", "observationdate"]
filtered_table = dataset.to_table(
    columns=columns_needed,
    filter=(
        (pc.field("parameter") == "WaterAbund (#/ml)") &
        (pc.field("parameter_imisdasid") == 4688) &
        (pc.field("latitude") >= min_lat) &
        (pc.field("latitude") <= max_lat) &
        (pc.field("longitude") >= min_lon) &
        (pc.field("longitude") <= max_lon)
    )
)

df = filtered_table.to_pandas()

# Extract date (YYYY-MM) from observationdate
df['observationdate'] = pd.to_datetime(df['observationdate'])
df['date_ym'] = df['observationdate'].dt.strftime('%Y-%m')

# Filter to target months
df = df[df['date_ym'].isin(target_dates)]

# Keep only the columns we need
df = df[['aphiaid', 'latitude', 'longitude', 'parameter_value', 'date_ym']]
df = df.rename(columns={'parameter_value': 'abundance', 'date_ym': 'period'})

print(f"\nFiltered data: {len(df)} rows")
print(f"Dates: {sorted(df['period'].unique())}")
print(f"Lat range: {df['latitude'].min():.4f} to {df['latitude'].max():.4f}")
print(f"Lon range: {df['longitude'].min():.4f} to {df['longitude'].max():.4f}")

df.to_csv("dump.csv", index=False)
print(f"\nSaved to dump.csv")
print(df.head(10))


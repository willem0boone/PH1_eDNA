from urllib.parse import urlparse
import pyarrow
import pyarrow.fs
import pandas as pd
import pyarrow.compute as pc
import pyarrow.dataset as ds
occurrence_data = "https://s3.waw3-1.cloudferro.com/emodnet/emodnet_biology/12639/marine_biodiversity_observations_2026-02-26.parquet"

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

columns_needed = ["aphiaid", "latitude", "longitude", "parameter", "parameter_value"]
filtered_table = dataset.to_table(
    columns=columns_needed,
    filter=(
        (pc.field("parameter") == "WaterAbund (#/ml)") &
        (pc.field("parameter_imisdasid") == 4688)
    )
)

df = filtered_table.to_pandas()
df.to_csv("dump.csv")



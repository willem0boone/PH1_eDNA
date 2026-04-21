from urllib.parse import parse_qs, urlparse

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.fs as fs

occurrence_data = "https://datalab.dive.edito.eu/data-explorer?source=https://s3.waw3-1.cloudferro.com/emodnet/emodnet_biology/12639/marine_biodiversity_observations_2026-02-26.parquet"

# --- Parse source URL ---
outer_url = urlparse(occurrence_data)
source_url = parse_qs(outer_url.query).get("source", [occurrence_data])[0]
parsed_url = urlparse(source_url)

host = parsed_url.hostname
bucket_name = parsed_url.path.split('/')[1]
key = '/'.join(parsed_url.path.split('/')[2:])

print("host =", host)
print("bucket_name =", bucket_name)
print("key =", key)

# --- S3 filesystem ---
s3 = fs.S3FileSystem(
    endpoint_override=host,
    anonymous=True
)

dataset_path = f"{bucket_name}/{key}"

dataset = ds.dataset(
    dataset_path,
    filesystem=s3,
    format="parquet"
)

print("-" * 50)
print(dataset.schema)
print("-" * 50)

# --- Filters ---
dasid = 4687
parameter = "WaterAbund (#/ml)"

filter_expression = (
        (pc.field("parameter_imisdasid") == dasid)
        &
        (pc.field("parameter") == parameter)
)

# --- Query ---
filtered_table = dataset.to_table(
    columns=["parameter", "datetime"],
    filter=filter_expression
)

# --- Output ---
for row in filtered_table.slice(0, 10).to_pylist():
    print(row)

print(f"\nFiltered rows for parameter_imisdasid={dasid}: {filtered_table.num_rows}")


col = filtered_table["datetime"]

oldest = pc.min(col).as_py()
youngest = pc.max(col).as_py()

print(oldest, youngest)



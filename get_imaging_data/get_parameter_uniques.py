from urllib.parse import urlparse
import pyarrow as pa
import pyarrow.fs as fs
import pyarrow.dataset as ds
import pyarrow.compute as pc

# --- Source parquet file ---
occurrence_data = "https://s3.waw3-1.cloudferro.com/emodnet/emodnet_biology/12639/marine_biodiversity_observations_2026-02-26.parquet"

# --- Parse URL into S3 components ---
parsed_url = urlparse(occurrence_data)
host = parsed_url.hostname
bucket_name = parsed_url.path.split('/')[1]
key = '/'.join(parsed_url.path.split('/')[2:])

print("host =", host)
print("bucket_name =", bucket_name)
print("key =", key)

# --- Connect to S3 (anonymous access) ---
s3 = fs.S3FileSystem(endpoint_override=host, anonymous=True)
s3_path = f"{bucket_name}/{key}"

# --- Load dataset ---
dataset = ds.dataset(s3_path, filesystem=s3, format="parquet")

# --- Scan ONLY the 'parameter' column ---
table = dataset.to_table(columns=["parameter"])

# --- Compute value counts ---
counts_struct = pc.value_counts(table["parameter"])

# Convert struct array → table
counts_table = pa.Table.from_arrays(
    [counts_struct.field("values"), counts_struct.field("counts")],
    names=["parameter", "count"]
)

# --- Optional: sort descending by count ---
counts_table = counts_table.sort_by([("count", "descending")])

# --- Convert to pandas for easy viewing/export ---
df_counts = counts_table.to_pandas()

# --- Save to CSV ---
df_counts.to_csv("parameter_counts.csv", index=False)

# --- Print preview ---
print(df_counts.head(20))
print("Total unique parameters:", len(df_counts))



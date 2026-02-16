import os
import shutil
from databricks.sdk.runtime import dbutils
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from source_pkg.utils import get_config
import mlflow

def main():
    """
    Ingests data from a CSV source into a Delta table, enabling change data feed and applying liquid clustering.

    This function orchestrates the data ingestion process, including:
    - Initializing MLflow for autologging.
    - Retrieving configuration parameters like table name, source path, and metadata volume.
    - Ensuring the necessary directories exist for the Delta table and its metadata.
    - Copying the source data to the Delta table's location.
    - Reading the data stream from the source CSV files.
    - Inferring column types and applying a schema.
    - Adding an 'ingested_at' timestamp column.
    - Writing the stream to a Delta table, enabling change data feed and setting a checkpoint location.
    - Optimizing the Delta table using liquid clustering on the 'id' column.
    - Verifying the ingestion by counting the total rows in the table.

    """
    #auto log
    mlflow.langchain.autolog() 

    spark = SparkSession.builder.getOrCreate()
    config = get_config()
    
    TABLE_NAME = config.table_name
    SOURCE_PATH = config.source_path
    METADATA_VOLUME =  config.metadata_volume 
    DELTA_SOURCE_PATH = f"{METADATA_VOLUME}/rawdata/{TABLE_NAME}"   

    # Ensure the Volume directory exists for this specific table
    dbutils.fs.mkdirs(DELTA_SOURCE_PATH)
    dbutils.fs.mkdirs(f"{METADATA_VOLUME}/schemas/{TABLE_NAME}")
    dbutils.fs.mkdirs(f"{METADATA_VOLUME}/checkpoints/{TABLE_NAME}")    
    # Volumes act like normal folders
    shutil.copytree(SOURCE_PATH, DELTA_SOURCE_PATH, dirs_exist_ok=True)

    display(dbutils.fs.ls(DELTA_SOURCE_PATH))

    print(f"Starting ingestion into {TABLE_NAME}...")
    (spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{METADATA_VOLUME}/schemas/{TABLE_NAME}") 
        .load(DELTA_SOURCE_PATH)
        .withColumn("ingested_at", current_timestamp())
        .writeStream
        .option("tableProperty.delta.enableChangeDataFeed", "true")
        .option("checkpointLocation", f"{METADATA_VOLUME}/checkpoints/{TABLE_NAME}")
        .trigger(availableNow=True)
        .toTable(TABLE_NAME))
    
    print(f"Optimizing table {TABLE_NAME} with Liquid Clustering...")
    spark.sql(f"ALTER TABLE  {TABLE_NAME} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    spark.sql(f"ALTER TABLE {TABLE_NAME} CLUSTER BY (id)")
    spark.sql(f"OPTIMIZE {TABLE_NAME}")

    # 4. Verify count
    count = spark.table(TABLE_NAME).count()
    print(f"Ingestion complete. Total rows in {TABLE_NAME}: {count}")

if __name__ == "__main__":
    main()

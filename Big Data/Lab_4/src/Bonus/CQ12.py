import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, when, min as spark_min, coalesce, lit, to_json, struct
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# ==============================================================================
# PREAMBLE
# ==============================================================================

# IP address of the machine running Kafka and the HDFS NameNode.
MASTER_NODE_IP = "172.27.140.17"

# Kafka Topics and Server Configuration
KAFKA_BOOTSTRAP_SERVERS = f"{MASTER_NODE_IP}:9092"
INPUT_TOPIC = "btc-price"
HIGHER_OUTPUT_TOPIC = "btc-price-higher"
LOWER_OUTPUT_TOPIC = "btc-price-lower"

# HDFS path for reliable, fault-tolerant checkpointing on the cluster
HDFS_NAMENODE_URI = f"hdfs://{MASTER_NODE_IP}:9000"
CHECKPOINT_LOCATION_BASE = f"{HDFS_NAMENODE_URI}/user/nqthinh/spark_checkpoints/bonus"

# ==============================================================================
# MAIN LOGIC
# ==============================================================================

def main():
    # 1. Initialize Spark Session for YARN deployment
    spark = SparkSession.builder \
        .appName("BonusPriceWindowAnalysis") \
        .config("spark.sql.shuffle.partitions", 4) \
        .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session created.")

    # 2. Read and Parse Input Stream from Kafka
    schema = StructType([
        StructField("symbol", StringType()),
        StructField("price", DoubleType()),
        StructField("timestamp", StringType())
    ])

    df_base = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", INPUT_TOPIC) \
        .load() \
        .select(from_json(col("value").cast("string"), schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", col("timestamp").cast("timestamp"))
    
    print("Kafka input stream prepared.")

    # 3. Perform Stateful Stream-Stream Self-Join
    df_left = df_base.alias("left")
    df_right = df_base.alias("right")

    # Apply watermarking to allow Spark to manage and prune state
    df_left_watermarked = df_left.withWatermark("timestamp", "30 seconds")
    df_right_watermarked = df_right.withWatermark("timestamp", "10 seconds")

    # Join condition requires an equality predicate (symbol) and a time-bound range
    join_expression = expr("""
        left.symbol = right.symbol AND
        right.timestamp > left.timestamp AND
        right.timestamp <= left.timestamp + interval 20 seconds
    """)
    
    df_joined = df_left_watermarked.join(df_right_watermarked, join_expression, "leftOuter")
    print("Performing stateful stream-stream self-join.")

    # 4. Calculate Time to First Higher/Lower Price with Millisecond Precision.
    #    Cast timestamps to double for precise subtraction to preserve fractional seconds.
    df_with_diff = df_joined.withColumn(
        "time_diff_secs",
        col("right.timestamp").cast("double") - col("left.timestamp").cast("double")
    )
    
    df_agg = df_with_diff.groupBy("left.timestamp", "left.symbol").agg(
        spark_min(when(col("right.price") > col("left.price"), col("time_diff_secs"))).alias("min_higher_diff"),
        spark_min(when(col("right.price") < col("left.price"), col("time_diff_secs"))).alias("min_lower_diff")
    )

    # 5. Finalize Results, using 20.0 as the default if no match was found
    df_results = df_agg.select(
        col("left.timestamp").alias("timestamp"),
        coalesce(col("min_higher_diff"), lit(20.0)).cast(DoubleType()).alias("higher_window"),
        coalesce(col("min_lower_diff"), lit(20.0)).cast(DoubleType()).alias("lower_window")
    )
    print("Calculated higher and lower price windows.")

    # 6. Write Results to their Respective Kafka Topics
    # Higher price window stream
    query_higher = df_results.select(to_json(struct("timestamp", "higher_window")).alias("value")) \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("topic", HIGHER_OUTPUT_TOPIC) \
        .option("checkpointLocation", os.path.join(CHECKPOINT_LOCATION_BASE, "higher")) \
        .start()
    print(f"Writing to Kafka topic: {HIGHER_OUTPUT_TOPIC}")
    
    # Lower price window stream
    query_lower = df_results.select(to_json(struct("timestamp", "lower_window")).alias("value")) \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("topic", LOWER_OUTPUT_TOPIC) \
        .option("checkpointLocation", os.path.join(CHECKPOINT_LOCATION_BASE, "lower")) \
        .start()
    print(f"Writing to Kafka topic: {LOWER_OUTPUT_TOPIC}")

    spark.streams.awaitAnyTermination()

# ==============================================================================
# DRIVER CODE
# ==============================================================================

if __name__ == "__main__":
    main()
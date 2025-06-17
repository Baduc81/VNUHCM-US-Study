from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, ArrayType

def get_zscore_schema():
    window_schema = StructType([
        StructField("window", StringType(), False),
        StructField("zscore_price", DoubleType(), False)
    ])
    return StructType([
        StructField("timestamp", TimestampType(), False),
        StructField("symbol", StringType(), False),
        StructField("zscores", ArrayType(window_schema), False)
    ])

def create_spark_session() -> SparkSession:
    return (SparkSession.builder
            .appName("KafkaMongoDBLoader")
            .config("spark.jars.packages",
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                    "org.mongodb.spark:mongo-spark-connector_2.12:10.5.0")
            .getOrCreate())

def read_kafka_stream(spark: SparkSession,
                      topic: str,
                      server: str = "localhost:9092"):
    return (spark.readStream
                 .format("kafka")
                 .option("kafka.bootstrap.servers", server)
                 .option("subscribe", topic)
                 .option("startingOffsets", "latest")
                 .load())

def parse_and_explode(df, schema):
    parsed = (df.select(from_json(col("value").cast("string"), schema)
                        .alias("data"))
                .select("data.*"))

    return (parsed
            .select(col("timestamp"),
                    col("symbol"),
                    explode(col("zscores")).alias("z"))
            .select("timestamp",
                    "symbol",
                    col("z.window").alias("window"),
                    col("z.zscore_price").alias("zscore_price")))

def write_to_mongo(stream_df, window):
	return (stream_df.writeStream
            .format("mongodb")
            .option("uri", "mongodb://mongodb:27017")
            .option("database", "btc")
            .option("collection", "btc-price-zscore")
            .option("checkpointLocation", "./chk/load/")
            .outputMode("append")
            .start())
	
def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("ERROR")

    schema = get_zscore_schema()

    kafka_df = read_kafka_stream(spark, "btc-price-zscore")
    exploded_df = parse_and_explode(kafka_df, schema)

    query = write_to_mongo(exploded_df, "all")
    query.awaitTermination()

if __name__ == "__main__":
    main()


from pyspark.sql import SparkSession, Window, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, ArrayType

def create_schema():

    # ĐỊNH NGHĨA SCHEMA CHO DỮ LIỆU ĐỌC TỪ TOPIC btc-price
    SCHEMA_EXTRACT = StructType([
        StructField("timestamp", TimestampType(), False),
        StructField("symbol", StringType(), False),
        StructField("price", DoubleType(), False)
    ])

    # ĐỊNH NGHĨA SCHEMA CHO DỮ LIỆU ĐỌC TỪ TOPIC btc-price-moving
    # SCHEMA_MOVING = StructType([
    #     StructField("timestamp", TimestampType(),False),
    #     StructField("symbol", StringType(),False),
    #     StructField("windows", ArrayType(
    #         StructType([
    #             StructField("window", StringType(),False),
    #             StructField("avg_price", DoubleType(),False),
    #             StructField("std_price", DoubleType(),False)
    #         ])
    #     ),False)
    # ])


    WINDOW_SCHEMA = StructType([
        StructField("window", StringType(),False),
        StructField("avg_price", DoubleType(),False),
        StructField("std_price", DoubleType(),False)
    ])
    
    SCHEMA_MOVING = StructType([
        StructField("timestamp", TimestampType(),False),
        StructField("symbol", StringType(),False),
        StructField("windows", ArrayType(WINDOW_SCHEMA),False)
    ])

    return SCHEMA_EXTRACT, SCHEMA_MOVING

def create_SparkSession():
   # KHỞI TẠO SPARKSESSION
    spark = SparkSession.builder \
        .appName("KafkaSparkStreaming") \
        .config("spark.sql.streaming.checkpointLocation", "./.checkpoint") \
        .config("spark.sql.debug.maxToStringFields", "100") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
        .getOrCreate() 
    spark.sparkContext.setLogLevel("ERROR")
    return spark

def read_from_kafka(
        spark,
        topic,
        server="localhost:9092",
    ):
    
    # ĐỌC STREAM TỪ KAFKA
    stream = spark \
        .readStream \
        .format("Kafka") \
        .option("kafka.bootstrap.servers",server) \
        .option("failOnDataLoss", "false") \
        .option("subscribe", topic) \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", "200") \
        .load()
    
    return stream

def create_extract_parsed_df(
        stream,
        SCHEMA
    ):

    # PARSE DATA SANG FORMAT CỦA SCHEMA
    parsed_df = stream \
        .select(
            from_json(col("value").cast("string"), SCHEMA).alias("data"),
        ) \
        .select(
            col("data.*")
        )
    
    return parsed_df.withWatermark("timestamp","10 seconds")

def create_moving_parsed_df(
        stream,
        SCHEMA
    ):

    # PARSE DATA SANG FORMAT CỦA SCHEMA
    parsed_df = stream \
        .select(
            from_json(col("value").cast("string"), SCHEMA).alias("data"),
        ) \
        .select(
            col("data.*")
        )

    # EXPLODE DỮ LIỆU ĐỂ THỰC HIỆN INNER JOIN Ở BƯỚC SAU
    exploded_parsed_df = parsed_df.select(
        col("timestamp"),
        col("symbol"),
        explode(col("windows")).alias("windows_attr")
    ).select(
        col("timestamp"),
        col("symbol"),
        col("windows_attr.window").alias("window"),
        col("windows_attr.avg_price").alias("avg_price"),
        col("windows_attr.std_price").alias("std_price")
    )

    return exploded_parsed_df.withWatermark("timestamp","10 seconds")

def create_join_df(
        extract_parsed_df, 
        moving_parsed_df
    ):

    # CẤU TRÚC DỮ LIỆU BAN ĐẦU
    # extract_parsed_df
    #  |-- timestamp: timestamp (nullable = false)
    #  |-- symbol: string (nullable = false)
    #  |-- price: double (nullable = false)

    # moving_parsed_df
    #  |-- timestamp: timestamp (nullable = false)
    #  |-- symbol: string (nullable = false)
    #  |-- window: string (nullable = false)
    #  |-- avg_price: double (nullable = false)
    #  |-- std_price: double (nullable = false)

    extract_parsed_df = extract_parsed_df\
                        .select(
                            col("timestamp").alias("timestamp1"),
                            col("symbol").alias("symbol1"),
                            col("price")
                        )
    moving_parsed_df = moving_parsed_df\
                    .select(
                        col("timestamp").alias("timestamp2"),
                        col("symbol").alias("symbol2"),
                        col("window"),
                        col("avg_price"),
                        col("std_price")
                    )
    
    joined_df = extract_parsed_df.join(
        moving_parsed_df,
        (extract_parsed_df.symbol1 == moving_parsed_df.symbol2) &
        (extract_parsed_df.timestamp1 == moving_parsed_df.timestamp2),
        "inner"
    ).select(
        col("timestamp1").alias("timestamp"),
        col("symbol1").alias("symbol"),
        col("window"),
        col("price"),
        col("avg_price"),
        col("std_price")
    )

    return joined_df

def create_zscore_df(
        df
    ):

    # THỰC HIỆN TÍNH TOÁN ZSCORE CHO TỪNG TABLE
    zscore_df = df.withColumn(
        "zscore_price",
        when(
            (col("std_price") > 0.00001), 
            (col("price") - col("avg_price")) / col("std_price")
        ).otherwise(lit(0.0))
    ) \
    .select(
        col("timestamp"),
        col("symbol"),
        col("window"),
        col("zscore_price")
    )

    return zscore_df

def create_format_output(
        df
    ):

    # LOẠI BỎ CÁC TRỪNG LẶP KHI THỰC HIỆN PHÉP JOIN, THỰC HIỆN LẤY GIÁ TRỊ TRUNG BÌNH KHI TÍNH TOÁN
    output_df = df \
        .groupBy("timestamp", "symbol", "window") \
        .agg(
            avg("zscore_price").alias("zscore_price")
        ) \
        .groupBy("timestamp", "symbol") \
        .agg(
            collect_list(
                struct(
                    col("window"),
                    col("zscore_price")
                )
            ).alias("zscores")
        )
    

    return output_df

def write_to_kafka(
        df,
        server="localhost:9092",
        topic="btc-price-zscore"
    ):
    
    # GHI DATAFRAME VÀO KAFKA
    # NOTE: KAFKA YÊU CẦU DỮ LIỆU GỬI VỀ PHẢI CÓ COLUMN VALUE
    writting = df \
        .select(
            to_json(
                struct(
                    col("timestamp"),
                    col("symbol"),
                    col("zscores")
                )
            ).alias("value")
        )\
        .writeStream \
        .format("Kafka") \
        .option("kafka.bootstrap.servers",server) \
        .option("topic", topic) \
        .outputMode("append") \
        .start()
        # .option("outputMode","update") \
    
    writting.awaitTermination()

def run():
    
    # STEP 1: TẠO SPARK SESSION, SET LOG LEVEL VỀ ERROR (CONSOLE CHỈ HIỆN CÁC LOG LEVEL ERROR, WARN SẼ ĐƯỢC TẮT)
    spark = create_SparkSession()
    
    # STEP 2: TẠO STREAM KAFKA, ĐỌC DỮ LIỆU TỪ TOPIC (STREAM MẶC ĐỊNH ĐỌC TỪ KAFKA, ĐỌC TỪ TOPIC btc-price)
    SCHEMA_EXTRACT, SCHEMA_MOVING = create_schema()
    
    # STEP 3: ĐỌC STREAM TỪ CÁC TOPIC CỦA KAFKA
    # Topic btc-price:
    extract_stream = read_from_kafka(spark, topic="btc-price")
    extract_parsed_df = create_extract_parsed_df(extract_stream,SCHEMA_EXTRACT)

    # Topic btc-price-moving:
    moving_stream = read_from_kafka(spark, topic="btc-price-moving")
    moving_parsed_df = create_moving_parsed_df(moving_stream,SCHEMA_MOVING)

    # STEP 4: JOIN 2 DATAFRAME
    joined_df = create_join_df(extract_parsed_df, moving_parsed_df)

    # STEP 5: TÍNH TOÁN Z-SCORE
    zscore_df = create_zscore_df(joined_df)

    # STEP 6: THỰC HIỆN FORMAT CHO OUTPUT ĐẦU RA
    output_df = create_format_output(zscore_df)

    # STEP 7: GHI DỮ LIỆU VÀO TOPIC bt-price-zscore
    write_to_kafka(output_df)

if __name__ == '__main__':
    run()
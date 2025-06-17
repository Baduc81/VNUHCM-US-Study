from pyspark.sql import SparkSession, Window, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

def create_schema_window():

    # ĐỊNH NGHĨA SCHEMA CHO DỮ LIỆU ĐỌC TỪ TOPIC
    SCHEMA = StructType([
        StructField("timestamp", TimestampType(), False),
        StructField("symbol", StringType(), False),
        StructField("price", DoubleType(), False)
    ])

    # LƯU TRỮ THAM CHIẾU WINDOWS
    WINDOWS = {
        "30s": "30 SECONDS",
        "1m": "1 MINUTE",
        "5m": "5 MINUTES",
        "15m": "15 MINUTES",
        "30m": "30 MINUTES",
        "1h": "1 HOUR",
    }

    return SCHEMA, WINDOWS

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
        server="localhost:9092",
        topic="btc-price"
    ):
    
    # ĐỌC STREAM TỪ KAFKA
    stream = spark \
        .readStream \
        .format("Kafka") \
        .option("kafka.bootstrap.servers",server) \
        .option("failOnDataLoss", "false") \
        .option("subscribe", topic) \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", "100") \
        .load()
    
    return stream

def create_parsed_df(
        stream,
        SCHEMA
    ):
    # PARSES DATA SANG DẠNG FORMAT THEO SCHEMA ĐƯỢC ĐỊNH NGHĨA
    parsed_df = stream \
        .select(
            from_json(col("value").cast("string"), SCHEMA).alias("data"),
        ) \
        .select(
            to_timestamp(col("data.timestamp")).alias("timestamp"),
            col("data.symbol"),
            col("data.price"),
        )

    return parsed_df

def process_window_df(
        df, 
        window_key, 
        window_value
    ):
    
    # TẠO WATERMARK TIMESTAMP THỐNG NHẤT CHO TOÀN BỘ STREAMING DATAFRAME ĐỂ THỰC HIỆN UNION
    df_watermark = df.withWatermark("timestamp","10 SECONDS")

    # TẠO BỘ CỬA SỔ TRƯỢT ĐỂ THỰC HIỆN TÍNH TOÁN DỰA TRÊN BỘ SỐ
    SLIDING_WINDOWS = {
        "30 SECONDS": "6 SECONDS",
        "1 MINUTE": " 12 SECONDS", 
        "5 MINUTES": "1 MINUTE",
        "15 MINUTES": "3 MINUTES",
        "30 MINUTES": "6 MINUTES",
        "1 HOUR": "12 MINUTES"
    }

    # FORMAT DỮ LIỆU ĐẦU RA CHO MỘT WINDOW CỤ THỂ:
    # out_df
    #  |-- timestamp: timestamp (nullable = false)
    #  |-- symbol: string (nullable = false)
    #  |-- window: string (nullable = false)
    #  |-- avg_price: double (nullable = false)
    #  |-- std_price: double (nullable = false)

    return df_watermark \
        .groupBy(
            window(col("timestamp"),window_value,SLIDING_WINDOWS.get(window_value,"10 SECONDS")),
            col("symbol"),
        ) \
        .agg(
            avg("price").alias("avg_price"),
            stddev("price").alias("std_price"),
        ) \
        .select(
            col("window.end").alias("timestamp"),
            col("symbol"),
            lit(window_key).alias("window"),
            col("avg_price"),
            coalesce(col("std_price"), lit(0.0)).alias("std_price")
        )

def create_format_output(
        df,
        windows
    ):

    all_windows_df = None

    # THỰC HIỆN TẠO CÁC DATAFRAME THEO CÁC WINDOW
    for key, value in windows.items():
        window_df = process_window_df(df, key, value)

        if all_windows_df is None:
            all_windows_df = window_df
        else:
            # THỰC HIỆN UNION CÁC DATAFRAME ĐỂ THỰC HIỆN XUẤT RA KẾT QUẢ CUỐI VỚI FORMAT MONG MUỐN
            all_windows_df = all_windows_df.union(window_df)



    # FORMAT DỮ LIỆU ĐẦU RA ĐỂ GHI VÀO TOPIC btc-price-moving:
    # out_df
    #  |-- timestamp: timestamp (nullable = false)
    #  |-- symbol: string (nullable = false)
    #  |-- windows: list (nullable = false)
    #       struct: json (nulllable = false)
    #       |-- window: double (nullable = false)
    #       |-- avg_price: double (nullable = false)
    #       |-- std_price: double (nullable = false)


    return all_windows_df \
        .groupBy(
            col("timestamp"),
            col("symbol")
        ) \
        .agg(
            collect_list(
                struct(
                    col("window"),
                    col("avg_price"),
                    col("std_price")
                )
            ).alias("windows")
        ) \
        .select(
            col("timestamp"),
            col("symbol"),
            col("windows")
        )

def write_to_kafka(
        df,
        server="localhost:9092",
        topic="btc-price-moving"
    ):
    
    # GHI DATAFRAME VÀO KAFKA
    # NOTE: KAFKA YÊU CẦU DỮ LIỆU GỬI VỀ PHẢI CÓ COLUMN VALUE
    writting = df \
        .select(
            to_json(
                struct(
                    col("timestamp"),
                    col("symbol"),
                    col("windows")
                )
            ).alias("value")
        )\
        .writeStream \
        .format("Kafka") \
        .option("kafka.bootstrap.servers",server) \
        .option("topic", topic) \
        .outputMode("update") \
        .start()
    
    writting.awaitTermination()

def run():
    
    # STEP 1: TẠO SPARK SESSION, SET LOG LEVEL VỀ ERROR (CONSOLE CHỈ HIỆN CÁC LOG LEVEL ERROR, WARN SẼ ĐƯỢC TẮT)
    spark = create_SparkSession()
    
    # STEP 2: TẠO STREAM KAFKA, ĐỌC DỮ LIỆU TỪ TOPIC (STREAM MẶC ĐỊNH ĐỌC TỪ KAFKA, ĐỌC TỪ TOPIC btc-price)
    stream_data = read_from_kafka(spark)
    
    # STEP 3: TẠO CÁC CONNSTANT SCHEMA VÀ WINDOWS
    SCHEMA, WINDOWS = create_schema_window()
    
    # STEP 4: ĐỊNH DẠNG DỮ LIỆU ĐƯỢC ĐỌC TỪ KAFKA
    parsed_df = create_parsed_df(stream_data,SCHEMA)
    
    # STEP 5: ĐỊNH DẠNG DỮ LIỆU THU ĐƯỢC THÀNH DẠNG DỮ LIỆU MONG MUỐN
    final_df = create_format_output(parsed_df,WINDOWS)
    
    # STEP 6: XUẤT final_df VÀO TOPIC btc-price-moving CỦA KAFKA
    write_to_kafka(df=final_df)

if __name__ == '__main__':
    run()
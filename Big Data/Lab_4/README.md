# Chạy Zookeeper
```bash
/opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties
```

# Chạy Kafka server
```bash
/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties
```


# Tạo topic
```bash
/opt/kafka/bin/kafka-topics.sh --create --topic btc-price --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --create --topic btc-price-moving --bootstrap-server localhost:9092
/opt/kafka/bin/kafka-topics.sh --create --topic btc-price-zscore --bootstrap-server localhost:9092
```


# Thay đổi cấu hình topic (ví dụ, thay đổi thời gian giữ tin nhắn):
```bash
/opt/kafka/bin/kafka-topics.sh --alter --topic btc-price --bootstrap-server localhost:9092 --config retention.ms=3600000
```

# Kiểm tra topic đã tạo
```bash
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

# Xóa topic
```bash
/opt/kafka/bin/kafka-topics.sh --delete --topic btc-price --bootstrap-server localhost:9092
```

# Dùng Kafka console consumer để kiểm tra dữ liệu trong topic (--from-beginning hoặc startingOffsets="earliest" để đọc từ đầu):
```bash
/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic btc-price --from-beginning
```


# Dùng producer để gửi dữ liệu
```bash
/opt/kafka/bin/kafka-console-producer.sh --broker-list localhost:9092 --topic btc-price
```

# Extract
```bash
python src/Extract/CQ12.py
```

# Transform
```bash
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 src/Transform/CQ12_moving.py # moving
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 src/Transform/CQ12_zscore.py # zscore
```


# Load
```bash
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.mongodb.spark:mongo-spark-connector_2.12:10.5.0 \
  --conf spark.mongodb.connection.uri="mongodb://mongodb:27017" \
  --conf spark.mongodb.read.connection.uri="mongodb://mongodb:27017" \
  --conf spark.mongodb.write.connection.uri="mongodb://mongodb:27017" \
	src/Load/CQ12.py
```

# Bonus
```bash
spark-submit \
  --master yarn \
  --deploy-mode client \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.4 \
  src/Bonus/CQ12.py > bonus.log 2> err_bonus.log &
```

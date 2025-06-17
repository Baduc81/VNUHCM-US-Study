# Hướng dẫn chạy code phân tích và dự đoán NYC Taxi Trip Duration

## Yêu cầu
- **Môi trường**: Python 3.10+, Spark 3.x, Hadoop 3.x, Jupyter Notebook.
- **Thư viện**: `pyspark`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `graphviz`.
- **Phần mềm**: Graphviz (dùng để trực quan hóa cây).
- **Dữ liệu**: `train.csv`, `test.csv` (từ dataset NYC Taxi).

Cài đặt thư viện:
```bash
pip install pyspark pandas numpy matplotlib seaborn graphviz jupyter
```

Cài đặt Graphviz:
- **Ubuntu**:
  ```bash
  sudo apt-get install graphviz
  ```
- **macOS**:
  ```bash
  brew install graphviz
  ```
- **Windows**: Tải từ https://graphviz.org/download/ và thêm vào PATH.

## Các bước thực hiện

### 1. Khởi động HDFS và YARN
Khởi động HDFS và YARN để quản lý dữ liệu và tài nguyên:
```bash
$HADOOP_HOME/sbin/start-dfs.sh
$HADOOP_HOME/sbin/start-yarn.sh
```

Kiểm tra trạng thái:
```bash
hdfs dfsadmin -report
yarn node -list
```

### 2. Upload dữ liệu lên HDFS
Tạo thư mục và upload file `train.csv`, `test.csv` lên HDFS:
```bash
hdfs dfs -mkdir -p /hcmus/nyc-taxi-trip-duration
hdfs dfs -put train.csv /hcmus/nyc-taxi-trip-duration/
hdfs dfs -put test.csv /hcmus/nyc-taxi-trip-duration/
```

Kiểm tra:
```bash
hdfs dfs -ls /hcmus/nyc-taxi-trip-duration
```

### 3. Xóa kết quả cũ (nếu có)
Nếu đã chạy code trước đó, xóa thư mục kết quả để tránh xung đột:
```bash
hdfs dfs -rm -r /hcmus/nyc-taxi-trip-duration/predictions
```

### 4. Phân tích tương quan đặc trưng
Chạy từng cell trong file `CorrelationMatrix.ipynb` để:
- Tính toán ma trận tương quan giữa các đặc trưng.
- Xác định các đặc trưng phù hợp (ví dụ: `pickup_longitude`, `pickup_latitude`, `dropoff_longitude`, `dropoff_latitude`).

### 5. Huấn luyện, dự đoán và trực quan hóa
Chạy từng cell trong file `LowLevelDecisionTreeNYCTaxi.ipynb` để:
- **Khám phá dữ liệu**: Thống kê (mean, min, max, Q1, Q2, Q3), kiểm tra missing data.
- **Huấn luyện**: Xây dựng Decision Tree (Variance Reduction, `max_depth=3`).
- **Đánh giá**: Tính RMSE, MAE, R² trên tập validation.
- **Dự đoán**: Dự đoán trên tập test và lưu vào HDFS (`/hcmus/nyc-taxi-trip-duration/predictions`).
- **Trực quan hóa**: Vẽ cây quyết định bằng hàm `visualize_decision_tree`.

### 6. Kiểm tra kết quả dự đoán
Xem 10 dòng cuối của file kết quả trên HDFS:
```bash
hdfs dfs -cat /hcmus/nyc-taxi-trip-duration/predictions/part-00000 | tail -n 10
```

Kết quả có định dạng:
```
id,trip_duration
id3004672,959.1234
...
```

### 7. Tải và gộp file kết quả
Gộp tất cả file `part-*` trong thư mục kết quả và tải về local:
```bash
hdfs dfs -getmerge /hcmus/nyc-taxi-trip-duration/predictions predictions.csv
```

Kiểm tra file:
```bash
head predictions.csv
```

# Hướng dẫn chạy code phân loại Lừa đảo Thẻ tín dụng Credit Card Fraud

> Áp dụng cho cả 3 phần: Structured API, MLib for RDD, và Low-level Operations.

## Yêu cầu 
### Môi trường chạy
- `Python 3.1x`
- `Apache Hadoop 3.x`
- `Apache Spark 3.x`
- `Java SDE 8.0`

### Thư viện
- `findshark` : Để tìm đường dẫn của các thành phần môi trường chạy liên quan đến Apache Spark
- `pyspark` : Môi trường làm việc với Apache Spark viết bằng Python. Được cài sẵn với Apache Spark

## Các bước chạyy

### Khởi động HDFS

Khởi động namenode và datanode trên HDFS bằng câu lệnh sau

```bash
$HADOOP_HOME/sbin/start-dfs.sh
```

### Cào dữ liệu

Cào bộ dữ liệu `creditcardfraud.csv` trực tiếp từ Kaggle sử dụng `cURL`

```bash
!curl -L -o ./creditcardfraud.zip\
  https://www.kaggle.com/api/v1/datasets/download/mlg-ulb/creditcardfraud

!python -m zipfile -e 'creditcardfraud.zip' './'
!rm 'creditcardfraud.zip'
```

> Không yêu cầu đẩy file từ local lên HDFS, do mã nguồn đã xử lý và có thể lấy bộ dữ liệu (trong file `.csv`) từ local (sử dụng thư viện `os` để lấy đường dẫn tương đối và sử dụng cú pháp `file:///` để báo hiệu file cần truy cập là file cục bộ)
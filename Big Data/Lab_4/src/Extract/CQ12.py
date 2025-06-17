import time
import json
import requests
import logging
from datetime import datetime, timezone
import math
import threading
import queue
from kafka import KafkaProducer

# Cấu hình logging để ghi log vào file 'extract.log'
logging.basicConfig(level=logging.INFO, filename='extract.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cấu hình API và Kafka
API_ENDPOINT = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
FREQUENCY_PER_100MS = 1  # 1 lần/100ms mỗi luồng
SLEEP_TIME = 0.1 / FREQUENCY_PER_100MS  # 0.1 giây
NUM_THREADS = 2  # Số luồng fetch data

# Biến kiểm soát dừng
# stop_event là cơ chế thread-safe để báo hiệu các luồng dừng khi nhấn Ctrl+C, đảm bảo dừng chương trình sạch.
stop_event = threading.Event()

# Tạo session để tái sử dụng kết nối HTTP Session 
# Tái sử dụng kết nối đến Binance API, giảm thời gian thiết lập kết nối mỗi lần gọi (~10-20ms).
session = requests.Session()

def fetch_btc_price():
    """
    Fetch the current BTC price from Binance API.
    Returns a dictionary with 'symbol' and 'price' if successful,
    or None if there was an error or invalid data.
    """
    # start = time.time()
    try:
        response = session.get(API_ENDPOINT, timeout=5) # Timeout 5 giây ngăn chương trình treo quá lâu nếu mạng chậm.
        response.raise_for_status()
        data = response.json()
        
        # Kiểm tra định dạng dữ liệu
        if not isinstance(data, dict) or 'symbol' not in data or 'price' not in data:
            logger.warning("Invalid data format received from API")
            return None
        
        if not isinstance(data['symbol'], str):
            logger.warning("Symbol is not a string")
            return None
        
        try:
            data['price'] = float(data['price'])
        except (ValueError, TypeError):
            logger.warning("Price is not a valid number")
            return None
        
        # logger.debug(f"Fetch took: {(time.time() - start) * 1000:.2f} ms")
        return data
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logger.warning(f"Rate limit exceeded, waiting 1 second")
            time.sleep(1)
        else:
            logger.error(f"HTTP error: {e}")
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return None
    # finally:
    #     logger.debug(f"Total fetch time: {(time.time() - start) * 1000:.2f} ms")

def format_iso8601(now, frequency_per_100ms):
    """
    Format a timestamp to ISO 8601 with millisecond precision.
    """
    precision_ms = 100 / frequency_per_100ms
    milliseconds = now.microsecond // 1000
    rounded_milliseconds = math.floor(milliseconds / precision_ms) * precision_ms
    return now.replace(microsecond=int(rounded_milliseconds * 1000)).isoformat().replace('+00:00', 'Z')

def create_record():
    """
    Create a record with the current BTC price and timestamp.
    """
    data = fetch_btc_price()
    if data:
        now = datetime.now(timezone.utc)
        timestamp = format_iso8601(now, FREQUENCY_PER_100MS)
        return {
            "symbol": data["symbol"],
            "price": float(data["price"]),
            "timestamp": timestamp
        }
    return None

def fetch_worker(queue, thread_id):
    """
    Worker thread to fetch data and put records into queue.
    """
    while not stop_event.is_set():  # # Chạy đến khi nhận tín hiệu dừng
        try:
            loop_start = time.time()
            record = create_record()
            if record:
                queue.put(record)   # Đẩy record vào queue thread-safe
                logger.info(f"Thread {thread_id} created record: {record}")
            
            elapsed = time.time() - loop_start  # Thời gian thực hiện fetch
            time.sleep(max(0, SLEEP_TIME - elapsed))    # Điều chỉnh time sleep để đảm bảo tần suất
        except Exception as e:
            logger.error(f"Thread {thread_id} error: {e}")
            if stop_event.is_set():
                break

def main():
    # Khởi tạo queue và producer
    record_queue = queue.Queue() # Queue thread-safe để lưu record
    producer = KafkaProducer(bootstrap_servers='localhost:9092',
                            value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    
    # Khởi động các luồng fetch
    threads = []
    for i in range(NUM_THREADS):
        t = threading.Thread(target=fetch_worker, args=(record_queue, i))
        t.daemon = True     # # Daemon thread dừng khi main thread dừng
        t.start()
        threads.append(t)
    
    # Đếm record mỗi giây
    record_count = 0
    start_time = time.time()
    
    try:
        while True:
            try:
                record = record_queue.get(timeout=1)
                producer.send('btc-price', value=record)       # Gửi record vào Kafka topic btc-price
                producer.flush()                                    # Đảm bảo gửi ngay lập tức
                record_count += 1
                logger.info(f"Sent to Kafka: {record}")
            except queue.Empty:
                pass
            
            current_time = time.time()
            if current_time - start_time >= 1.0: # Mỗi giây kiểm tra số record đã gửi
                logger.info(f"Records sent in last second: {record_count}")
                record_count = 0
                start_time = current_time
    
    except KeyboardInterrupt:
        logger.info("Stopping program...")
        stop_event.set()  # Báo hiệu các thread dừng
        
        # Chờ các thread kết thúc
        for t in threads:
            t.join(timeout=2)  # Chờ tối đa 2 giây mỗi thread
        
        # Đóng producer
        producer.close()
        
        # Đóng session và flush logging
        session.close()
        logging.shutdown()  # Xả buffer log và đóng file
        
        logger.info("Program stopped successfully")

if __name__ == "__main__":
    main()
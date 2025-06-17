from mrjob.job import MRJob
from mrjob.step import MRStep

class MRInnerJoin(MRJob):

    def mapper(self, _, line):
        # Tách dòng thành tên bảng, khóa và giá trị
        table_name, key, value = line.split()
        yield key, (table_name, value)

    def reducer(self, key, values):
        prices = []
        quantities = []

        # Phân loại các giá trị dựa trên bảng nguồn
        for table_name, value in values:
            if table_name == 'FoodPrice':
                prices.append(value)
            elif table_name == 'FoodQuantity':
                quantities.append(value)

        # Thực hiện INNER JOIN
        # Chỉ phát ra nếu có giá trị từ cả hai bảng cho khóa hiện tại
        if prices and quantities:

            # Kết hợp từng giá trị từ FoodPrice với từng giá trị từ FoodQuantity
            for price_val in prices:
                for quantity_val in quantities:
                    yield key, f"{price_val} {quantity_val}"

if __name__ == '__main__':
    MRInnerJoin.run()
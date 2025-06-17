from mrjob.job import MRJob

class DistanceCalculation(MRJob):

    def configure_args(self):
        super(DistanceCalculation, self).configure_args()
        self.add_passthru_arg(
            '--q', type=int, default=4,
            help='Query point value (default: 4)'
        )

    def mapper(self, _, line):

        # Lấy giá trị query point từ tham số dòng lệnh
        query_point = self.options.q

        point, coord = line.strip().split('\t')
        coord = int(coord)
        
        # Tính khoảng cách tuyệt đối
        distance = abs(coord - query_point)
        
        # Phát ra (distance, point)
        yield distance, point

    def reducer(self, key, values):
        
        # Thu thập tất cả các điểm có cùng khoảng cách
        points = ' '.join(values)
        
        # Phát ra (distance, list of points)
        yield key, points

if __name__ == '__main__':
    DistanceCalculation.run()
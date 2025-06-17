from mrjob.job import MRJob
import ast

class KMeansClustering(MRJob):

    def configure_args(self):
        super(KMeansClustering, self).configure_args()
        self.add_passthru_arg(
            '--centers', type=str, default='[2, 6, 9]',
            help='List of initial center coordinates, e.g., "[2, 6, 9]"'
        )

    def __init__(self, *args, **kwargs):
        super(KMeansClustering, self).__init__(*args, **kwargs)
        # Chuyển đổi chuỗi tham số thành danh sách số
        self.centers = ast.literal_eval(self.options.centers)

    def mapper(self, _, line):

        # Tách điểm và tọa độ từ mỗi dòng
        point, coord = line.strip().split('\t')
        coord = int(coord)

        # Tìm trung tâm gần nhất
        min_dist = float('inf')
        closest_center = None
        for center in self.centers:
            dist = abs(coord - center)
            if dist < min_dist:
                min_dist = dist
                closest_center = center

        # Phát ra (trung tâm, (điểm, tọa độ))
        yield (closest_center, (point, coord))

    def reducer(self, center, values):

        # Tính trung tâm mới dựa trên trung bình của các tọa độ
        points = []
        coords_sum = 0
        count = 0
        
        for point, coord in values:
            points.append(point)
            coords_sum += coord
            count += 1

        new_center = coords_sum / count if count > 0 else center

        # Phát ra (old_center, new_center, danh sách điểm)
        joined_points = ' '.join(points)
        yield f"{center} {new_center:.2f}", joined_points
        # yield (center, new_center), points

if __name__ == '__main__':
    KMeansClustering.run()
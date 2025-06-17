from mrjob.job import MRJob
from mrjob.protocol import RawProtocol
import statistics

class MR(MRJob):

    OUTPUT_PROTOCOL = RawProtocol

    def mapper(self, _, line):    # type: ignore

        if '\t' in line:
            group, point = line.strip().split('\t')
        
            yield group, int(point)

    def reducer(self, group, points):     # type: ignore

        lst = list(points)
        center = round(sum(lst) / len(lst), 2)
        centroid = statistics.median(lst)

        yield group, f"{center:.2f}\t{centroid:g}"

if __name__ == '__main__':
    MR.run()
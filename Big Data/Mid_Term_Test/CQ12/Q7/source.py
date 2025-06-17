#!/usr/bin/env python3
# Author: Phan Bá Đức
# MSSV: 22120071

from mrjob.job import MRJob
from mrjob.step import MRStep

class digitalImage(MRJob):
    def mapper(self, _, line):
        if line.strip():
            try:
                for item in line.split():
                    pixel_value = int(item.strip())
                    yield pixel_value, 1
            except ValueError:
                pass

    def combiner(self, item, counts):
        total_count = sum(counts)
        yield item, total_count

    def reducer(self, item, counts):
        total_count = sum(counts)
        yield None, (item, total_count)

    def final_reducer(self, _, counts):
        counts_dict = {}
        pixel_max = 0

        for item, count in counts:
            counts_dict[item] = count
            if item > pixel_max:
                pixel_max = item

        for pixel in range(pixel_max + 1):
            yield pixel, counts_dict.get(pixel, 0)
    
    def steps(self):
        return [
            MRStep(mapper=self.mapper,
                   combiner=self.combiner,
                   reducer=self.reducer),
            MRStep(reducer=self.final_reducer)
        ]

if __name__ == '__main__':
    digitalImage.run()

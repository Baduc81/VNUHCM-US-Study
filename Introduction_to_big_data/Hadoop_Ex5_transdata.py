#!/usr/bin/env python3
# Author: Phan Bá Đức
# MSSV: 22120071

from mrjob.job import MRJob
from mrjob.step import MRStep
import sys
from itertools import combinations

class TransactionProcessor(MRJob):
    def mapper(self, _, line):
        sys.stderr.write("Processing line: %s\n" % line)

        if line.strip():
            try:
                transaction_id, items = line.split('\t')
                items = items.strip().split(' ')
                for pair in combinations(items, 2):
                    sorted_pair = tuple(sorted(pair))
                    yield sorted_pair, 1

            except ValueError:
                sys.stderr.write("Error processing line: %s\n" % line)

    def combiner(self, pair, counts):
        yield pair, sum(counts)

    def reducer(self, itemset, counts):
        total_count = sum(counts)

        '''
        Lý do truyền theo kiểu None, (total_count, itemset) là vì MR làm việc theo kiểu
        key-value, truyển None làm key để về sau có thể group lại (vì có chung key)
        Nếu cứ truyền kiểu (total_count, itemset) thì sẽ không group lại được

        Lý do truyền (total_count, itemset) là vì trong bước reducer_find_max, ta cân lấy ra giá trị max
        của total_count. Ta sẽ dùng hàm MAX, mà hàm max lại so sánh theo kiểu tuple theo thứ tự
        (first element, second element). Nên ta cần truyền theo kiểu tuple để có thể so sánh được.
        Nếu ta truyền kiểu (itemset, total_count) thì phải viết thêm lambda x: x[1] để lấy ra
        giá trị thứ 2 trong tuple để so sánh, làm phức tạp thêm.
        '''
        yield None, (total_count, itemset)

    def reducer_find_max(self, _, itemsets_count):
        # Tìm cặp itemset có số lần xuất hiện lớn nhất
        max_count, max_itemset = max(itemsets_count)

        itemset_str = ' '.join(max_itemset) 
        yield itemset_str, max_count

    def steps(self):
        return [
            MRStep(
                mapper=self.mapper,
                combiner=self.combiner,
                reducer=self.reducer,
            ),
            MRStep(
                reducer=self.reducer_find_max
            )
        ]


if __name__ == '__main__':
    TransactionProcessor.run()
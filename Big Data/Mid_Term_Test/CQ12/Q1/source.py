#!/usr/bin/env python3
# Author: Phan Bá Đức
# MSSV: 22120071

from mrjob.job import MRJob
from mrjob.step import MRStep
# import logging

# logging.basicConfig(level=logging.INFO, filename='source.log', format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

class TransactionProcessor(MRJob):
    def mapper(self, _, line):
        if line.strip():
            try:
                transaction_id, item = line.split('\t')
                # logging.info(f"Parsed: {transaction_id} -> {item}")
                yield (transaction_id, item.strip()), 1
            except ValueError:
                pass

    def combiner(self, id_item, counts):
        # logging.info(f"combiner: {id_item}, {counts}")
        total_count = sum(counts)
        yield id_item, total_count

    def reducer(self, id_item, counts):
        id, item = id_item
        # logging.info(f"reducer: {id}, {item}, {counts}")
        total_count = sum(counts)
        yield id, (item, total_count)

    def reducer_group(self, id, item_counts):
        # logging.info(f"reducer_group: {id}, {item_counts}")
        item_counts = list(item_counts)

        # Sắp xếp theo count giảm dần, nếu bằng nhau thì theo thứ tự từ điển
        sorted_items = sorted(item_counts, key=lambda x: (-x[1], x[0]))
        yield id, sorted_items

        # result = [f"[{item}, {count}]" for item, count in sorted_items]
        # yield id, ''.join(result)

    def steps(self):
        return [
            MRStep(mapper=self.mapper,
                   combiner=self.combiner,
                   reducer=self.reducer),
            MRStep(reducer=self.reducer_group)
        ]
if __name__ == '__main__':
    TransactionProcessor.run()
                
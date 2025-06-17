from mrjob.job import MRJob
from mrjob.protocol import RawProtocol

def compute_item_price(item: str):
    discount_rate = 0.8 if item.endswith('*') else 1
    full_price = float(sum(1 for ch in item if ch.isalpha()))

    return discount_rate * full_price

class MR(MRJob):
    OUTPUT_PROTOCOL = RawProtocol

    def mapper(self, _, line):  # type: ignore
        
        if '\t' not in line:
            return
        
        tid, item = line.strip().split('\t')
        price = compute_item_price(item)

        yield tid, price

    def reducer(self, key, values):

        total = sum(values)
        yield key, f"{total:g}"

if __name__ == '__main__':
    MR.run()
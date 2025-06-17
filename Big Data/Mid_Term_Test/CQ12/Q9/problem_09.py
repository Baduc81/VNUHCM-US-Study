from mrjob.job import MRJob
from mrjob.protocol import RawProtocol

def left_outer_join(key, left_vals, right_vals):
    if not left_vals:
        return
    
    if right_vals:
        for left_val in left_vals:
            for right_val in right_vals:
                yield (key, f"{left_val}\t{right_val}")
    else:
        for left_val in left_vals:
            yield key, f"{left_val}\tnull"

class MR(MRJob):
    
    OUTPUT_PROTOCOL = RawProtocol

    def mapper(self, _, line):  # type: ignore
        if '\t' not in line:
            return
        
        parts = line.strip().split('\t')
        
        if len(parts) != 3:
            return
            
        table, key, value = parts
        yield key, (table, value)

    def reducer(self, key, values):
        food_price_vals = []
        food_quantity_vals = []

        for table, value in values:
            if table == 'FoodPrice':
                food_price_vals.append(value)
            else:
                food_quantity_vals.append(value)

        for result in left_outer_join(key, food_price_vals, food_quantity_vals):
            yield result


if __name__ == '__main__':
    MR.run()
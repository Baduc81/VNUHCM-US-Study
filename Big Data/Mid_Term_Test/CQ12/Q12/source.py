#!/usr/bin/env python3
# Author: Phan Bá Đức
# MSSV: 22120071

from mrjob.job import MRJob

class FullOuterJoin(MRJob):
    def mapper(self, _, line):
        if line.strip():
            try:
                table, key, value = line.split()
                yield key, (table, value)
            except ValueError:
                pass

    def reducer(self, key, values):
        price = "null"
        quantity = "null"
        for table, value in values:
            if table == 'FoodPrice':
                price = value
            elif table == 'FoodQuantity':
                quantity = value

        yield key, f"{price} {quantity}"

if __name__ == '__main__':
    FullOuterJoin.run()
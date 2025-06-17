from mrjob.job import MRJob
from mrjob.step import MRStep

class Question10(MRJob):
    def mapper(self, _, line):
        if line == '':
            return
        table, key, value = line.split()
        yield key, (table, value)

    def reducer(self, key, values):
        prices = []
        quantities = []

        for table, value in values:
            if table == "FoodPrice":
                prices.append(value)
            else:
                quantities.append(value)

        if len(quantities) == 0:
            return
        elif len(prices) == 0:
            for q in quantities:
                yield key, f"null {q}"
        else:
            for q in quantities:
                for p in prices:
                    yield key, f"{p} {q}"


if __name__ == '__main__':
    Question10.run()
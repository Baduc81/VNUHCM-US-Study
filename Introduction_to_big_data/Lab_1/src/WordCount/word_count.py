#!/usr/bin/env python3
from mrjob.job import MRJob
import re

class LetterCount(MRJob):
    valid_letters = set("afjghcmus")

    def mapper(self, _, line):
        pattern = r'[a-zA-Z]+'
        words = re.findall(pattern, line)

        for word in words:
            if word:
                first_char = word[0].lower()
                if first_char in self.valid_letters:
                    yield first_char, 1

    def combiner(self, letter, counts):
        """Combiner function: tổng hợp cục bộ để giảm lượng dữ liệu truyền qua mạng"""
        yield letter, sum(counts)

    def reducer(self, letter, counts):
        yield letter, sum(counts)

if __name__ == '__main__':
    LetterCount.run()

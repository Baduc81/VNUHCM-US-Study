from mrjob.job import MRJob


class Question3(MRJob):
    def mapper(self, _, line):
        if line == '':
            return
        transaction_id, items = line.split('\t')
        items = items.split(' ')
        for item in set(items):
            yield item, transaction_id

    def reducer(self, item, transaction_ids):
        unique_transaction_ids = set()
        for transaction_id in transaction_ids:
            unique_transaction_ids.add(transaction_id)
        if len(unique_transaction_ids) > 1:
            yield item, list(unique_transaction_ids)

if __name__ == '__main__':
    Question3.run()

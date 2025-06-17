from mrjob.job import MRJob
from itertools import combinations

class AprioriJob(MRJob):
    def __init__(self, *args, **kwargs):
        super(AprioriJob, self).__init__(*args, **kwargs)

    def configure_args(self):
        super(AprioriJob, self).configure_args()
        self.add_passthru_arg(
            '--minsup', type=float, default=0.5, help='Minimum support threshold (decimal)'
        )
        self.add_passthru_arg(
            '--total-transactions', type=int, default=0, help='Total number of transactions'
        )

    def mapper(self, _, line):

        items = [x.strip() for x in line.split('\t')[1].split(' ')]
        n = len(items)

        for i in range(1, n+1):
            for subset in combinations(items, i):
                itemset = ' '.join(sorted(subset))
                yield itemset, 1

    def reducer(self, key, values):
        support_count = sum(values)
        # Kiểm tra nếu support_count >= total_transactions * minsup
        minsup_cnt = self.options.total_transactions * self.options.minsup
        if support_count >= minsup_cnt:
            yield key, support_count

if __name__ == '__main__':
    AprioriJob.run()
from mrjob.job import MRJob
from datetime import datetime

class Question8(MRJob):
    def mapper(self, _, line):
        if line == '':
            return
        phone, _, start, end, std = line.split('|')
        start_d = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end_d = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        call_time = (end_d - start_d).total_seconds()

        if std == "1":
            yield phone, int(call_time)

    def reducer(self, phone, call_times):
        total_call_time = sum(call_times)
        if total_call_time // 60 > 60:
            yield phone, total_call_time // 60

if __name__ == '__main__':
    Question8.run()

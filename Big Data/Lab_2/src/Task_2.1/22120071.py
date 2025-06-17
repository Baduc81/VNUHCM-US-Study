from mrjob.job import MRJob
from datetime import datetime, timedelta
import csv

column_names = None

class Ex21(MRJob):
    def mapper(self, _, inp):
        global column_names

        # first line in csv file
        if inp.startswith("index"):
            column_names = inp.split(',')
            return

        row = list(csv.reader([inp]))[0]
        date, category = "", ""
        revenue = 0
        is_shipped = False # only consider row with status = shipped

        # this assert should be True
        # assert len(column_names) == len(row), f"{len(column_names)}, {len(row)}, {row}"
        
        for i in range(len(column_names)):
            col = column_names[i].strip().lower()
            row_val = row[i].strip()

            if col == 'date':
                date = row_val
                dt = datetime.strptime(date, '%m-%d-%y')
            elif col == 'category':
                category = row_val
            elif col == 'amount':
                if row[i].strip() != '':
                    revenue = float(row_val)
            elif col == 'status':
                is_shipped = row_val.lower() == 'shipped'
            
        if not is_shipped:
            return

        tomorrow = dt + timedelta(days=1)
        tomorrow_of_tomorrow = tomorrow + timedelta(days=1)

        yield (dt.strftime('%d/%m/%Y'), category), revenue
        yield (tomorrow.strftime('%d/%m/%Y'), category), revenue
        yield (tomorrow_of_tomorrow.strftime('%d/%m/%Y'), category), revenue

    def reducer(self, key, value):
        report_date, category = key
        yield (report_date, category, sum(value)), None

if __name__ == '__main__':
    Ex21.run()
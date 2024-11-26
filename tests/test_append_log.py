import datetime as dt
import pandas as pd

from stocktrace.src.storage.file import FileQuery, FileManager, TIMEZONE

FileManager.init()

test_path = 'stocktrace/tests/test_append_log.csv'
test_log = {'message': [f'{dt.datetime.now(TIMEZONE)} INFO TEST!!!!']}
test_log = pd.DataFrame(test_log)

query = FileQuery(test_path)
FileManager.append_file(query, test_log)
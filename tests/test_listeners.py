import pandas as pd

from stocktrace import Asset, TIMEZONE

def listener():
    print("I HAVE BEEN CALLED")

def listener2():
    print("I HAVE BEEN CALLED2")

def listener3():
    print("I HAVE BEEN CALLED3")

apple = Asset('AAPL')

apple.add_listener(listener)
apple.add_listener(listener2)
apple.add_listener(listener3)

data = pd.read_csv(apple.file_path, parse_dates=True)
data.index = pd.to_datetime(data.iloc[:,0])
data.index = data.index.tz_convert(TIMEZONE)
data.drop(columns=data.columns[0], axis=1, inplace=True)
data.drop(data.tail(3).index,inplace=True)
data.to_csv(apple.file_path)
apple.data.drop(apple.data.tail(3).index,inplace=True)

apple.update_data()
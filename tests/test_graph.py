import pandas as pd
import pyqtgraph as pg
import time

from stocktrace import Asset, AssetWidget, TIMEZONE

def drop():
    data = pd.read_csv(asset.file_path, parse_dates=True)
    data.index = pd.to_datetime(data.iloc[:,0])
    data.index = data.index.tz_convert(TIMEZONE)
    data.drop(columns=data.columns[0], axis=1, inplace=True)
    data.drop(data.tail(3).index,inplace=True)
    data.to_csv(asset.file_path)
    asset.data.drop(asset.data.tail(3).index,inplace=True)
    widget.update_data()

def update():
    asset.update_data()

asset = Asset('MSFT')
pg.mkQApp()

widget = AssetWidget(asset)
widget.show()

button1 = pg.QtWidgets.QPushButton('Drop 3 days worth of data')
button1.clicked.connect(drop)

button2 = pg.QtWidgets.QPushButton('Update data to current')
button2.clicked.connect(update)

widget.layout.addWidget(button1)
widget.layout.addWidget(button2)

pg.exec()
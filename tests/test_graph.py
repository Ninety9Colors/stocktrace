import pandas as pd
import pyqtgraph as pg
import time

from stocktrace import Asset, AssetWidget, TIMEZONE

def drop():
    data = asset.data
    data.drop(data.tail(3).index,inplace=True)
    asset.data.drop(asset.data.tail(3).index,inplace=True)
    widget.update_data()

def update():
    asset.update_data()

asset = Asset('BTC-USD',auto_save=False)
pg.mkQApp()

widget = AssetWidget(asset)
widget.show()

button1 = pg.QtWidgets.QPushButton('Drop 3 days worth of data')
button1.clicked.connect(drop)

button2 = pg.QtWidgets.QPushButton('Update data to current')
button2.clicked.connect(update)

widget.layout.addWidget(button1, 2,0)
widget.layout.addWidget(button2, 3,0)

pg.exec()
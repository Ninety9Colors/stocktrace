import pandas as pd
import pyqtgraph as pg
import time

from stocktrace import AssetManager, AssetWidget, TIMEZONE, IndicatorManager
from stocktrace.custom import SMA_TEN

def drop():
    data = widget.asset.data
    data.drop(data.tail(3).index,inplace=True)
    widget.asset.data.drop(widget.asset.data.tail(3).index,inplace=True)
    widget.update_data()

def update():
    widget.asset.update_data()

def switch():
    widget.set_asset(AssetManager.get('GOOG'))

def add_smas():
    widget.add_indicator('SMA_TEN')
    widget.add_indicator('SMA_TWENTY')

asset = AssetManager.get('BTC-USD')
pg.mkQApp()

widget = AssetWidget(asset)
widget.show()

button1 = pg.QtWidgets.QPushButton('Drop 3 days worth of data')
button1.clicked.connect(drop)

button2 = pg.QtWidgets.QPushButton('Update data to current')
button2.clicked.connect(update)

button3 = pg.QtWidgets.QPushButton('Switch to GOOG')
button3.clicked.connect(switch)

button4 = pg.QtWidgets.QPushButton('Add SMA10')
button4.clicked.connect(add_smas)

widget.layout.addWidget(button1, 2,0,1,2)
widget.layout.addWidget(button2, 3,0,1,2)
widget.layout.addWidget(button3, 4,0,1,2)
widget.layout.addWidget(button4, 5,0,1,2)

pg.exec()
import datetime as dt
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets

from stocktrace.utils import interval_to_timedelta, delta_to_seconds
from stocktrace.logging.logger import Logger as logger
from stocktrace.engine.asset import Asset

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, asset: Asset, *args, **kargs):
        super().__init__(*args, **kargs)
        self.__asset = asset

    @property
    def asset(self) -> Asset:
        return self.__asset
    
class _TimeframeWidget(QtWidgets.QWidget):
    def __init__(self, parent: 'AssetWidget', *args, **kargs) -> None:
        logger.debug(f'_TimeframeWidget.__init__ Making _TimeframeWidget with parent={parent}')
        super().__init__(*args, **kargs)

        self.setLayout(QtWidgets.QGridLayout())
        self.parent = parent
        self.labels = ['1wk', '1mo', '3mo', '6mo', '1y', '5y', 'Max']
        self.buttons = []
        for i,label in enumerate(self.labels):
            logger.info(f'Creating button with label {label}')
            button = QtWidgets.QPushButton(label)
            self.layout().addWidget(button, 0, i)
            button.clicked.connect(lambda checked, label=label: self.update_timeframe(label))
            self.buttons.append(button)
    
    def update_timeframe(self, text: str) -> None:
        self.parent.update_timeframe(text)

class AssetWidget(QtWidgets.QWidget):
    def __init__(self, asset: Asset, auto_update: bool = True, *args, **kargs) -> None:
        logger.debug(f'AssetWidget.__init__ Making AssetWidget with {asset}')
        super().__init__(*args, **kargs)
        self.__auto_update = auto_update
        self.__asset = asset
        self.__plot_widget = pg.PlotWidget()
        self.__plot_item = self.plot_widget.plotItem

        self.__layout = QtWidgets.QGridLayout()
        self.__timeframe = '1mo'
        self.setLayout(self.layout)
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(_TimeframeWidget(self))

        self.asset.add_listener(self._update_callback)
        self._init_graph()
    
    def update_data(self) -> None:
        logger.info(f'Updating data of {self.__repr__()}')
        x = np.array([x.timestamp() for x in self.asset.data.index.to_numpy()])
        y = self.asset.data['Close'].to_numpy() # plot CLOSE data
        logger.info(f'Retrieved x data:\n{x}')
        logger.info(f'Retrieved y data:\n{y}')
        self.line_item.setData(x, y)
        # self.candlestick_item.setData(x, y)
        self.update_timeframe()
    
    def update_timeframe(self, timeframe: str = None) -> None:
        logger.info(f'Updating timeframe of {self.__repr__()} to {timeframe}')
        if not timeframe:
            timeframe = self.timeframe
        data = self.line_item.getData()
        if (timeframe == 'Max'):
            self.plot_item.setXRange(data[0][0], data[0][-1])
        else:
            delta_seconds = delta_to_seconds(interval_to_timedelta(timeframe))
            self.plot_item.setXRange(data[0][-1] - delta_seconds, data[0][-1])
        self.plot_item.enableAutoRange(axis='y')
        self.plot_item.setAutoVisible(y=True)
        self.timeframe = timeframe

    @property
    def asset(self) -> Asset:
        return self.__asset
    
    @property
    def auto_update(self) -> bool:
        return self.__auto_update
    
    @auto_update.setter
    def auto_update(self, update: bool) -> None:
        self.__auto_update = update
    
    @property
    def plot_widget(self) -> pg.PlotWidget:
        return self.__plot_widget

    @property
    def plot_item(self) -> pg.PlotItem:
        return self.__plot_item
    
    @property
    def line_item(self) -> pg.PlotDataItem:
        return self.__line_item
    
    @property
    def candlestick_item(self) -> CandlestickItem:
        return self.__candlestick_item

    @property
    def layout(self) -> QtWidgets.QGridLayout:
        return self.__layout
    
    @property
    def timeframe(self) -> str:
        return self.__timeframe
    
    @timeframe.setter
    def timeframe(self, frame: str) -> None:
        self.__timeframe = frame

    def __repr__(self) -> str:
        return f'AssetWidget({self.asset})'

    def _init_graph(self) -> None:
        logger.info('Initializing graph data items...')
        self.plot_item.setAxisItems({'bottom': pg.DateAxisItem()})

        self.__line_item = pg.PlotDataItem()
        self.__candlestick_item = CandlestickItem(self.asset)

        logger.info('Adding items to plot item')
        self.plot_item.addItem(self.line_item)
        # self.plot_item.addItem(self.candlestick_item)

        self.update_data()
        self.update_timeframe('1mo')
    
    def _update_callback(self) -> None:
        if self.auto_update:
            logger.info(f'Auto updating {self.__repr__}')
            self.update_data()

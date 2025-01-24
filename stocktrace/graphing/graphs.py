import datetime as dt
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore

from stocktrace.utils import interval_to_timedelta, delta_to_seconds, BULLISH, BEARISH
from stocktrace.logging.logger import Logger as logger
from stocktrace.engine.asset import Asset

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, asset: Asset, hover: bool=True, *args, **kargs) -> None:
        logger.debug(f'CandlestickItem.__init__ Making CandlestickItem with asset={asset}')
        super().__init__(*args, **kargs)
        self.__asset = asset
        self.__candlesticks = []
        self.__picture = QtGui.QPicture()
        self.databox_picture = QtGui.QPicture()
        self.setAcceptHoverEvents(hover)
    
    def hoverMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        pos = event.pos()
        for i, (rect, line) in enumerate(self.candlesticks):
            full_rect = QtCore.QRectF(rect.x(), max(line.y1(), line.y2()), rect.width(), -line.length())
            if full_rect.contains(pos):
                logger.info(f'Hovering over candlestick with time {self.asset.data.index[i]}')

    def updatePicture(self) -> None:
        self.prepareGeometryChange()
        logger.info(f'Updating/Generating picture for {self.__repr__()}')
        
        painter = QtGui.QPainter(self.picture)
        close_data = self.asset.data['Close']
        open_data = self.asset.data['Open']
        high_data = self.asset.data['High']
        low_data = self.asset.data['Low']
        times = self.asset.data.index
        assert len(times) >= 2
        width = (times[1]-times[0]).total_seconds()/2
        assert len(times) == len(close_data)
        self.candlesticks.clear()
        for i in range(len(close_data)):
            open = open_data.iloc[i]
            close = close_data.iloc[i]
            high = high_data.iloc[i]
            low = low_data.iloc[i]
            time = times[i].timestamp()
            rect = QtCore.QRectF(time-width/2, open, width, close-open)
            line = QtCore.QLineF(time, low, time, high)
            top_line = QtCore.QLineF(time-width/2, high, time+width/2, high)
            bottom_line = QtCore.QLineF(time-width/2, low, time+width/2, low)
            self.candlesticks.append((rect, line))

            if close > open:
                painter.setPen(pg.mkPen('g'))
                painter.setBrush(pg.mkBrush('g'))
            else:
                painter.setPen(pg.mkPen('r'))
                painter.setBrush(pg.mkBrush('r'))
            
            painter.drawRect(rect)
            painter.drawLine(line)
            painter.drawLine(top_line)
            painter.drawLine(bottom_line)
        
        painter.end()
        

    def paint(self, p: QtGui.QPainter, *args) -> None:
        p.drawPicture(0,0,self.picture)
        p.drawPicture(0,0,self.databox_picture)
    
    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(self.picture.boundingRect())

    @property
    def asset(self) -> Asset:
        return self.__asset
    
    @property
    def candlesticks(self) -> list[QtCore.QRectF]:
        return self.__candlesticks
    
    @property
    def picture(self) -> QtGui.QPicture:
        return self.__picture

    def __repr__(self) -> str:
        return f'CandlestickItem({self.asset})' 
    
class _TimeframeWidget(QtWidgets.QWidget):
    def __init__(self, parent: 'AssetWidget', *args, **kargs) -> None:
        logger.debug(f'_TimeframeWidget.__init__ Making _TimeframeWidget with parent={parent}')
        super().__init__(*args, **kargs)

        self.setLayout(QtWidgets.QGridLayout())
        self.parent = parent
        self.labels = ['1wk', '1mo', '3mo', '6mo', '1y', '5y', 'Max']
        self.buttons = []
        self.setMaximumWidth(300)
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
        self.__timeframe = '1mo'

        self.asset.add_listener(self._update_callback)

        self.__plot_widget = pg.PlotWidget()
        self.__plot_item = self.plot_widget.plotItem
        self.__layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.plot_widget, 0, 0)
        self.layout.addWidget(_TimeframeWidget(self), 1, 0)

        self._init_graph()
    
    def update_data(self) -> None:
        logger.info(f'Updating data of {self.__repr__()}')
        x = np.array([x.timestamp() for x in self.asset.data.index.to_numpy()])
        y = self.asset.data['Close'].to_numpy() # plot CLOSE data
        logger.info(f'Retrieved x data:\n{x}')
        logger.info(f'Retrieved y data:\n{y}')
        self.line_item.setData(x, y)
        self.candlestick_item.updatePicture()
        padding = 0.1
        ymin = 0
        ymax = np.max(y)
        self.plot_item.setLimits(xMin=x[0]-padding*(x[-1]-x[0]), xMax=x[-1]+padding*(x[-1]-x[0]), yMin=ymin-padding*(ymax-ymin), yMax=ymax+padding*(ymax-ymin))
        self.update_timeframe()
    
    def update_timeframe(self, timeframe: str = None) -> None:
        # [x_start, x_end]
        def get_y_minmax(x_start: int, x_end: int, high: np.ndarray, low: np.ndarray, timestamps: np.ndarray) -> tuple[float, float]:
            mask = (timestamps >= x_start) & (timestamps <= x_end)
            low = low[mask]
            high = high[mask]
            return np.min(low), np.max(high)
        
        if not timeframe:
            timeframe = self.timeframe
        logger.info(f'Updating timeframe of {self.__repr__()} to {timeframe}')
        data = self.asset.data
        timestamps = np.array([x.timestamp() for x in data.index.to_numpy()])
        delta_seconds = timestamps[-1]-timestamps[0] if timeframe == 'Max' else delta_to_seconds(interval_to_timedelta(timeframe))
        start_x = timestamps[-1] - delta_seconds
        end_x = timestamps[-1]
        start_y, end_y = get_y_minmax(start_x, end_x, data['High'].to_numpy(), data['Low'].to_numpy(), timestamps)

        logger.info(f'Updating x range to {timeframe}: {start_x} to {end_x}')
        logger.info(f'Updating y range to {timeframe}: {start_y} to {end_y}')
        self.plot_item.setXRange(start_x, end_x)
        self.plot_item.setYRange(start_y, end_y)
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
        self.plot_item.addItem(self.candlestick_item)

        self.update_data()
        self.update_timeframe('1mo')
    
    def _update_callback(self) -> None:
        if self.auto_update:
            logger.info(f'Auto updating {self.__repr__}')
            self.update_data()

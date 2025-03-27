import datetime as dt
from typing import Optional
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore

from stocktrace.backtest import Backtest
from stocktrace.indicator import IndicatorManager, Indicator
from stocktrace.utils import TIMEZONE, interval_to_timedelta, delta_to_seconds, BULLISH, BEARISH, DARK
from stocktrace.logger import Logger as logger
from stocktrace.asset import Asset, AssetManager

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, parent: 'AssetWidget', asset: Asset, hover: bool=True, interval: str='1d',*args, **kargs) -> None:
        logger.debug(f'CandlestickItem.__init__ Making CandlestickItem with asset={asset}')
        super().__init__(*args, **kargs)
        self.__parent = parent
        self.__asset = asset
        self.__candlesticks = []
        self.__picture = QtGui.QPicture()
        self.__interval = interval
        self.default_opacity = 0.3
        self.hover_opacity = 0.8
        self.setAcceptHoverEvents(hover)
        self.setOpacity(self.default_opacity)
    
    def set_asset(self, new_asset: Asset) -> None:
        self.__asset = new_asset
    
    def hoverMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        pos = event.pos()
        for i, (rect, line) in enumerate(self.candlesticks):
            full_rect = QtCore.QRectF(rect.x(), max(line.y1(), line.y2()), rect.width(), -line.length())
            if full_rect.contains(pos):
                self.setOpacity(self.hover_opacity)
                logger.info(f'Hovering over candlestick with time {self.asset.data.index[i]}')
                break
            else:
                self.setOpacity(self.default_opacity)
    
    def hoverLeaveEvent(self, event):
        self.setOpacity(self.default_opacity)

    def updatePicture(self) -> None:
        self.prepareGeometryChange()
        logger.info(f'Updating/Generating picture for {self.__repr__()}')
        
        painter = QtGui.QPainter(self.picture)
        df = self.__parent.filtered_data()
        close_data = df['Close']
        open_data = df['Open']
        high_data = df['High']
        low_data = df['Low']
        times = df.index
        assert len(times) >= 2
        width = delta_to_seconds(interval_to_timedelta(self.__interval))/2
        assert len(times) == len(close_data)
        self.candlesticks.clear()
        for i in range(len(close_data)):
            open = open_data.iloc[i]
            close = close_data.iloc[i]
            high = high_data.iloc[i]
            low = low_data.iloc[i]
            assert open > 0
            assert close > 0
            assert high > 0
            assert low > 0
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
    def __init__(self, asset: Asset, auto_update: bool = True, start_date: Optional[dt.datetime]=dt.datetime.min.replace(tzinfo=TIMEZONE), end_date: Optional[dt.datetime]=dt.datetime.now(tz=TIMEZONE), *args, **kwargs) -> None:
        logger.debug(f'AssetWidget.__init__ Making AssetWidget with {asset}')
        super().__init__(*args, **kwargs)
        self.__start_date = start_date
        self.__end_date = end_date
        self.__auto_update = auto_update
        self.__asset = asset
        self.__timeframe = '1mo'
        self.__indicators = {}
        self.__indicator_items = {}
        self.__colors = ('y','g','r')
        self.__color_index = 0

        self.asset.add_listener(self._update_callback)

        self.__plot_widget = pg.PlotWidget()
        self.__plot_item = self.plot_widget.plotItem
        self.__plot_item.addLegend()
        self.__plot_item.legend.setScale(0.7)

        self.__layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.plot_widget, 0, 0, 1,2)
        self.layout.addWidget(_TimeframeWidget(self), 1, 0)

        self._init_graph()
    
    def add_indicator(self, name: str, pen: Optional[pg.QtGui.QPen]=None) -> None:
        if name in self.__indicators.keys():
            logger.warning(f'AssetWidget.add_indicator() Indicator {name} already added! Ignoring...')
            return
        if not pen:
            pen = pg.mkPen(self.__colors[self.__color_index])
            self.__color_index += 1
            if self.__color_index >= len(self.__colors):
                self.__color_index = 0

        self.__indicators[name] = IndicatorManager.get_indicator(name)(name)
        ind = self.__indicators[name]
        ind.init(self.asset.ticker_symbol)
        self.__indicator_items[name] = pg.PlotDataItem(pen=pen, name=name)
        logger.info(f'Adding indicator x: {np.array([x.timestamp() for x in ind.data.index])}')
        logger.info(f'Adding indicator y: {ind.data.values}')
        self.__indicator_items[name].setData(np.array([x.timestamp() for x in ind.data.index]), ind.data.values)
        self.plot_item.addItem(self.__indicator_items[name])

        logger.info(f'AssetWidget.add_indicator() Added and initialized indicator {self.__indicators[name]} to {self.__repr__()}')

    def remove_indicator(self, name: str) -> None:
        if name not in self.__indicators.keys():
            logger.warning(f'AssetWidget.remove_indicator() Indicator {name} not added! Ignoring...')
            return
        self.__indicators.pop(name)
        self.plot_item.removeItem(self.__indicator_items[name])
        self.__indicator_items.pop(name)
    
    def set_asset(self, new_asset: Asset) -> None:
        self.asset.remove_listener(self._update_callback)
        self.__asset = new_asset
        self.__asset.add_listener(self._update_callback) 
        self.__candlestick_item.set_asset(new_asset)
        self.update_data()
    
    def update_indicators(self) -> None:
        for name in self.__indicators.keys():
            assert name in self.__indicator_items.keys()
            assert self.__indicator_items[name] in self.plot_item.items
            self.__indicators[name].update_data(self.asset.ticker_symbol)
            ind = self.__indicators[name]
            self.__indicator_items[name].setData(np.array([x.timestamp() for x in ind.data.index]), ind.data.values)
    
    def update_data(self) -> None:
        logger.info(f'Updating data of {self.__repr__()}')
        data = self.filtered_data()
        x = np.array([x.timestamp() for x in data.index.to_numpy()])
        y = data['Close'].to_numpy() # plot CLOSE data
        logger.info(f'Retrieved x data:\n{x}')
        logger.info(f'Retrieved y data:\n{y}')
        self.line_item.setData(x, y)
        self.candlestick_item.updatePicture()
        self.update_indicators()
        padding = 0.05
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
        data = self.filtered_data()
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

    def filtered_data(self) -> pd.DataFrame:
        return self.asset.data.loc[(self.asset.data.index >= self.__start_date) & (self.asset.data.index <= self.__end_date)]

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

    @property
    def indicators(self) -> dict:
        return self.__indicators

    def __repr__(self) -> str:
        return f'AssetWidget({self.asset})'

    def _init_graph(self) -> None:
        logger.info('Initializing graph data items...')
        self.plot_item.setAxisItems({'bottom': pg.DateAxisItem()})

        self.__line_item = pg.PlotDataItem(name='Close Prices')
        self.__candlestick_item = CandlestickItem(self, self.asset)

        self.__candlestick_checkbox = QtWidgets.QCheckBox('Candlestick')
        self.__candlestick_checkbox.setChecked(True)
        self.__candlestick_checkbox.stateChanged.connect(lambda state: self.__candlestick_item.setVisible(state==2))
        self.layout.addWidget(self.__candlestick_checkbox, 1, 1)

        logger.info('Adding items to plot item')
        self.plot_item.addItem(self.line_item)
        self.plot_item.addItem(self.candlestick_item)

        self.update_data()
        self.update_timeframe('1mo')
    
    def _update_callback(self) -> None:
        if self.auto_update:
            logger.info(f'Auto updating {self.__repr__}')
            self.update_data()

class BacktestAssetWidget(AssetWidget):
    def __init__(self, backtest: Backtest, auto_update: bool = True, plot_indicators: bool=False,*args, **kwargs) -> None:
        assert backtest.completed
        super().__init__(AssetManager.get(backtest.get_traded_tickers()[0]), auto_update, backtest.start_date, backtest.end_date, *args, **kwargs)
        self.plot_item.setTitle(backtest.get_traded_tickers()[0])
        self.__backtest = backtest
        self.__trade_opacity = 0.8
        self.candlestick_item.default_opacity = 0.1
        self.__trade_items = []
        if plot_indicators:
            self._plot_indicators()
        self._plot_trades()
        self.update_timeframe('Max')
    
    def set_asset(self, new_asset: Asset) -> None:
        super().set_asset(new_asset)
        self.plot_item.setTitle(new_asset.ticker_symbol)
        for item in self.__trade_items:
            self.plot_item.removeItem(item)
        self._plot_trades()
    
    def _plot_indicators(self) -> None:
        for indicator in self.__backtest.algorithm.indicators:
            self.add_indicator(indicator.name)
    
    def _plot_trades(self) -> None:
        self.__trade_items.clear()
        for trade in self.__backtest.broker.get_position(self.asset.ticker_symbol).closed_trades:
            x1 = trade.entry_time.timestamp()
            y1 = trade.entry_cents/100
            x2 = trade.exit_time.timestamp()
            y2 = trade.exit_cents/100
            pen = pg.mkPen((BULLISH if (trade.is_long() == (trade.exit_cents > trade.entry_cents)) else BEARISH),
                   width=3,
                   style=QtCore.Qt.PenStyle.DotLine if trade.is_long() else QtCore.Qt.PenStyle.DashLine)
            line = pg.PlotDataItem([x1,x2],[y1,y2],pen=pen)
            line.setOpacity(self.__trade_opacity)
            self.plot_item.addItem(line)
            self.__trade_items.append(line)


class EquityWidget(QtWidgets.QWidget):
    def __init__(self, backtest: Backtest, statistics: pd.Series) -> None:
        assert backtest.completed
        super().__init__()
        self.__backtest = backtest
        self.__statistics = statistics
        self.setLayout(QtWidgets.QGridLayout())

        self.__plot_widget = pg.PlotWidget()
        self.__plot_widget.plotItem.setAxisItems({'bottom': pg.DateAxisItem()})
        self.__plot_widget.plotItem.addLegend()
        x = np.array([x.timestamp() for x in self.__backtest.equity.index])
        y = np.array(self.__backtest.equity.values)/100
        self.__equity_item = pg.PlotDataItem(x, y, name='Equity')

        self.__plot_widget.plotItem.addItem(self.__equity_item)
        self._plot_statistics()

        self.layout().addWidget(self.__plot_widget)

        padding = 0.05
        ymin = np.min(y)
        ymax = np.max(y)
        self.__plot_widget.plotItem.setLimits(xMin=x[0]-padding*(x[-1]-x[0]), xMax=x[-1]+padding*(x[-1]-x[0]), yMin=ymin-padding*(ymax-ymin), yMax=ymax+padding*(ymax-ymin))
    
    def _plot_statistics(self) -> None:
        peak = self.__statistics['Equity Peak $']
        peak_date = self.__statistics['Equity Peak Date'].timestamp()
        self.__equity_peak = pg.ScatterPlotItem([peak_date],[peak],size=10,pen=pg.mkPen('b'),name='Equity Peak')

        dd_begin = self.__statistics['Max Drawdown Begin']
        dd_end = self.__statistics['Max Drawdown End']
        self.__max_drawdown_item = pg.PlotDataItem([dd_begin.timestamp(), dd_end.timestamp()], [self.__backtest.equity[dd_begin]/100, self.__backtest.equity[dd_end]/100], pen=pg.mkPen('r'), name='Max Drawdown')

        self.__plot_widget.plotItem.addItem(self.__equity_peak)
        self.__plot_widget.plotItem.addItem(self.__max_drawdown_item)

    @property
    def plot_widget(self) -> pg.PlotWidget:
        return self.__plot_widget
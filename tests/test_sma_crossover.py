import datetime as dt
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore

from stocktrace import Backtest, Algorithm, Broker, SMACrossOver, Logger, LOG_LEVEL, TIMEZONE, AssetWidget, AssetManager

Logger.init(LOG_LEVEL.WARNING)

backtest = Backtest(
    algorithm=SMACrossOver(),
    broker=Broker(start_cash_cents=1000000, spread=0)
)

backtest.run(trace=True)
x = np.array([x.timestamp() for x in backtest.equity.index])
x1 = np.array([x.timestamp() for x in backtest.algorithm.sma1.data.index])
x2 = np.array([x.timestamp() for x in backtest.algorithm.sma2.data.index])

app = pg.Qt.mkQApp()
plot_widget: AssetWidget = AssetWidget(AssetManager.get('GOOG'))
plot_widget.plot_item.setAxisItems({'bottom': pg.DateAxisItem()})
# plot_widget.plotItem.plot(x, backtest.equity.values)
# plot_widget.plot_item.plot(x1, backtest.algorithm.sma1.data.values)
# plot_widget.plot_item.plot(x2, backtest.algorithm.sma2.data.values)

for trade in backtest.broker.get_position('GOOG').closed_trades:
    pen = pg.mkPen(('g' if (trade.is_long() == (trade.exit_cents > trade.entry_cents)) else 'r'),
                   width=2,
                   style=QtCore.Qt.PenStyle.DotLine if trade.is_long() else QtCore.Qt.PenStyle.DashLine)
    roi = pg.LineSegmentROI(((trade.entry_time.timestamp(), trade.entry_cents/100),(trade.exit_time.timestamp(), trade.exit_cents/100))
                            ,pen=pen)

    for handle in roi.getHandles():
        handle.hide()
    plot_widget.plot_item.addItem(roi)

plot_widget2 = pg.PlotWidget()
plot_widget2.plotItem.setAxisItems({'bottom': pg.DateAxisItem()})
x = np.array([x.timestamp() for x in backtest.equity.index])
y = np.array([x/10000 for x in backtest.equity.values])
plot_widget2.plotItem.plot(x,y)

plot_widget2.show()
plot_widget.show()
app.exec()
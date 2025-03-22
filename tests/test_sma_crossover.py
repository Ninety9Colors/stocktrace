import datetime as dt
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore

from stocktrace import Backtest, Algorithm, Broker, AlgorithmManager, Logger, LOG_LEVEL, TIMEZONE, AssetWidget, AssetManager, generate_statistics

Logger.init(LOG_LEVEL.WARNING)

backtest = Backtest(
    algorithm=AlgorithmManager.get_algorithm('SMACrossOver'),
    broker=Broker(start_cash_cents=1000000, spread=0),
    start_date=dt.datetime(2004, 8, 19, tzinfo=TIMEZONE),
    end_date=dt.datetime(2013, 3, 1, 23, 0, 0, tzinfo=TIMEZONE)
)

backtest.run(trace=True)
x = np.array([x.timestamp() for x in backtest.equity.index])
x1 = np.array([x.timestamp() for x in backtest.algorithm.sma1.data.index])
x2 = np.array([x.timestamp() for x in backtest.algorithm.sma2.data.index])
stats = generate_statistics(backtest.broker.closed_trades, backtest.equity, backtest.algorithm, backtest.start_date,backtest.end_date,'GOOG')
print(stats)

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

# 10.006341667453752
# 20.109832283135212
# 30.116173950588966
# 40.12386490899033
# 50.13020657644408
# 60.19996491843537
# 70.20630658588911
# 80.21264825334286
# 90.21898992079662
# Complete!
# Start                            2004-09-16 15:00:00-05:00
# End                              2013-03-01 16:00:00-05:00
# Duration                                3088 days 01:00:00
# Return %                                          752.7972
# Buy and Hold Return % (GOOG)                    606.360424
# Equity Final $                                    85279.72
# Equity Peak $                                      85365.1
# Equity Peak Date                 2013-02-19 16:00:00-05:00
# Win Rate %                                        54.83871
# Best Trade %                                     57.291561
# Worst Trade %                                   -16.399016
# Avg Trade %                                       2.691213
# Avg Win %                                         8.771782
# Avg Loss %                                       -4.692335
# Avg Trade Duration              31 days 14:11:36.774193548
# Max Trade Duration                       121 days 00:00:00
# Max Drawdown %                                  -34.083512
# Max Drawdown Begin               2006-02-15 16:00:00-05:00
# Max Drawdown End                 2007-07-03 15:00:00-05:00
# Avg Drawdown %                                   -5.226148
# Avg Drawdown Duration                     36 days 03:34:30
# Max Drawdown Duration                    680 days 23:00:00
# Algorithm                          Algorithm(SMACrossOver)
# dtype: object
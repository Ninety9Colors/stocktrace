import datetime as dt
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore

from stocktrace import Backtest, Algorithm, Broker, AlgorithmManager, Logger, LOG_LEVEL, TIMEZONE, BacktestPanel, AssetWidget, AssetManager, generate_statistics, BacktestAssetWidget, EquityWidget

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

panel = BacktestPanel(backtest, stats)

panel.show()
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
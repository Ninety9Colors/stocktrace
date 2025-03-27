from PyQt6.QtWidgets import QApplication
import datetime as dt

from stocktrace import BacktestPanel, AlgorithmManager, Backtest, Broker, generate_statistics, Logger, TIMEZONE

Logger.init(2)

backtest = Backtest(AlgorithmManager.get_algorithm('MultiSMACrossOver'),
                    Broker(1000000, spread=0),
                    start_date=dt.datetime(2004, 8, 19, tzinfo=TIMEZONE),
                    end_date=dt.datetime(2013, 3, 1, 23, 0, 0, tzinfo=TIMEZONE))
backtest.run()
stats = generate_statistics(backtest.broker.closed_trades,
                            backtest.equity,
                            backtest.algorithm,
                            backtest.start_date,
                            backtest.end_date,
                            'GOOG')

app = QApplication([])
panel = BacktestPanel(backtest, stats, True)
panel.show()
app.exec()
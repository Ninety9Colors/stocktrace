from stocktrace import Asset

apple = Asset('AAPL', '1wk')
tesla = Asset('TSLA', '1wk')
ms = Asset('MSFT', '1wk')
apple_daily = Asset('AAPL', '1d')
btc = Asset('BTC-USD', '1d')

apple.save_data()
tesla.save_data()
ms.save_data()
apple_daily.save_data()
btc.save_data()
import datetime as dt

from stocktrace import Broker, Order, Trade, Position, Asset, AssetManager, TIMEZONE

AssetManager.get('QBTS').save_data()

start_cents = 10000
spread = 0.05
broker = Broker(start_cents, spread=spread)

time_one = dt.datetime(2025, 1, 15, 23, 0, tzinfo=TIMEZONE)
buy_one = Order(broker, 'QBTS', 10, time_placed=time_one, limit_cents=560)
broker.place_order(buy_one)
broker.process_orders(time_one)

time_two = dt.datetime(2025, 3, 14, 23, 0, tzinfo=TIMEZONE)
sell_two = Order(broker, 'QBTS', -10, time_placed=time_two, limit_cents=905)
broker.place_order(sell_two)
broker.process_orders(time_two)

time_three = dt.datetime(2025, 3, 19, 23, 0, tzinfo=TIMEZONE)
buy_three = Order(broker, 'QBTS', 10, time_placed=time_three, limit_cents = 1058)
broker.place_order(buy_three)
broker.process_orders(time_three)

time_final = dt.datetime(2025, 3, 19, 23, 0, tzinfo=TIMEZONE)
print(broker.positions)
# {'QBTS': Position(QBTS, 10)}
print('Realized',broker.realized_pl(time_final)) # 3448
print('Unrealized',broker.unrealized_pl(time_final)) # 28
print(broker.equity) # 13476
print(broker.positions['QBTS'].closed_trades) # [Trade(QBTS, 10, self.__entry_cents=560, self.__exit_cents=905)]

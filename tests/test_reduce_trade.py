import datetime as dt

from stocktrace import Asset, AssetManager, Broker, Order, TIMEZONE

AssetManager.get('^GSPC').save_data()

t1 = dt.datetime(2025, 1, 2, 23, 0, tzinfo=TIMEZONE)
t2 = dt.datetime(2025, 1, 3, 23, 0, tzinfo=TIMEZONE)
t3 = dt.datetime(2025, 1, 6, 23, 0, tzinfo=TIMEZONE)

broker = Broker(100000000, spread=0.05)

order1 = Order(broker,'^GSPC', 10, time_placed=t1)
order2 = Order(broker,'^GSPC', 10, time_placed=t2)
order3 = Order(broker,'^GSPC', 10, time_placed=t3)

broker.place_order(order1)
broker.process_orders(t1)

broker.place_order(order2)
broker.process_orders(t2)

broker.place_order(order3)
broker.process_orders(t3)

print(broker.positions)
print(broker.positions['^GSPC'].trades)
# [Trade(^GSPC, 10, self.__entry_cents=619843, self.__exit_cents=None), Trade(^GSPC, 10, self.__entry_cents=618563, self.__exit_cents=None), Trade(^GSPC, 10, self.__entry_cents=628197, self.__exit_cents=None)]
print(broker.positions['^GSPC'].closed_trades)

print('\n------\n')

t4 = dt.datetime(2025, 3, 13, 23, 0, tzinfo=TIMEZONE)
order4 = Order(broker,'^GSPC', -5, time_placed=t4)
broker.place_order(order4)
broker.process_orders(t4)

print(broker.positions)
print(broker.positions['^GSPC'].trades)
print(broker.positions['^GSPC'].closed_trades)
print('\nrealized',broker.realized_pl(t4))
print('\nunrealized',broker.unrealized_pl(t4))

print('\n------\n')

t5 = dt.datetime(2025, 3, 18, 23, 0, tzinfo=TIMEZONE)
order5 = Order(broker,'^GSPC', -15, time_placed=t5)
broker.place_order(order5)
broker.process_orders(t5)

print(broker.positions)
print(broker.positions['^GSPC'].trades)
print(broker.positions['^GSPC'].closed_trades)
print('\nrealized',broker.realized_pl(t5))
print('\nunrealized',broker.unrealized_pl(t5))

# {'^GSPC': Position(^GSPC, 10)}
# [Trade(^GSPC, 10, self.__entry_cents=628197, self.__exit_cents=None)]
# [Trade(^GSPC, 5, self.__entry_cents=619843, self.__exit_cents=531473), Trade(^GSPC, 5, self.__entry_cents=619843, self.__exit_cents=537180), Trade(^GSPC, 10, self.__entry_cents=618563, self.__exit_cents=537180)]
                                                                             
# realized -1669297
# unrealized -386725
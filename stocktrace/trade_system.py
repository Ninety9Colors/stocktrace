import datetime as dt
from math import ceil, copysign, floor
import sys
from typing import Optional

from stocktrace.asset import AssetManager
from stocktrace.logger import Logger as logger
from stocktrace.utils import TIMEZONE

class ORDER_TYPE:
    MARKET = 0
    LIMIT = 1
    STOP_MARKET = 2
    STOP_LIMIT = 3

class Order:
    def __init__(self,
                broker: 'Broker',
                ticker_symbol: str, 
                shares: int, 
                type: Optional[ORDER_TYPE]=None,
                limit_cents: Optional[int]=None,
                stop_cents: Optional[int]=None,
                time_placed: Optional[dt.datetime]=None) -> None:
        logger.debug(f'Order.__init__ Initializing Order for {shares=} shares of {ticker_symbol=}')
        self.__broker = broker
        self.__ticker_symbol = ticker_symbol
        self.__shares = shares
        self.__time_placed = time_placed if time_placed else AssetManager.get(ticker_symbol).latest_date()
        self.__type = type
        self.__limit_cents = limit_cents
        self.__stop_cents = stop_cents
        self._init_type()
    
    def cancel(self) -> None:
        logger.info(f'Order for {self.__shares} shares of {self.__ticker_symbol} cancelled')
        self.__broker.orders.remove(self)
    
    def is_stop(self) -> bool:
        return self.__type == ORDER_TYPE.STOP_MARKET or self.__type == ORDER_TYPE.STOP_LIMIT
    
    def is_limit(self) -> bool:
        return self.__type == ORDER_TYPE.LIMIT or self.__type == ORDER_TYPE.STOP_LIMIT
    
    def is_market(self) -> bool:
        return self.__type == ORDER_TYPE.MARKET or self.__type == ORDER_TYPE.STOP_MARKET
    
    def is_long(self) -> bool:
        return self.__shares > 0
    
    def is_short(self) -> bool:
        return self.__shares < 0
    
    def _init_type(self) -> None:
        if self.__type is None:
            if self.__limit_cents:
                if self.__stop_cents:
                    self.__type = ORDER_TYPE.STOP_LIMIT
                else:
                    self.__type = ORDER_TYPE.LIMIT
            else:
                if self.__stop_cents:
                    self.__type = ORDER_TYPE.STOP_MARKET
                else:
                    self.__type = ORDER_TYPE.MARKET
    
    @property
    def ticker_symbol(self) -> str:
        return self.__ticker_symbol
    
    @property
    def shares(self) -> int:
        return self.__shares
    
    @property
    def time_placed(self) -> dt.datetime:
        return self.__time_placed
    
    @property
    def limit_cents(self) -> Optional[int]:
        return self.__limit_cents

    @property
    def stop_cents(self) -> Optional[int]:
        return self.__stop_cents

    @property
    def type(self) -> ORDER_TYPE:
        return self.__type
    
    @type.setter
    def type(self, value: ORDER_TYPE) -> None:
        self.__type = value

    def __repr__(self) -> str:
        return f'Order({self.__ticker_symbol}, {self.__shares} shares, {self.__type}, {self.__limit_cents}, {self.__stop_cents}, {self.__time_placed})'

class Broker:
    def __init__(self, start_cash_cents: int, trade_on_close: bool=False, spread: float=0.05) -> None:
        logger.debug(f'Broker.__init__ Initializing Broker with start cash {start_cash_cents}')
        self.__positions = {}
        self.__orders: list[Order] = []
        self.__cash = start_cash_cents
        self.__trade_on_close = trade_on_close
        self.__spread = spread
    
    def place_order(self, order: Order) -> None:
        if order.shares == 0:
            logger.info(f'Broker.place_order() Order for 0 shares of {order.ticker_symbol} ignored')
            return
        logger.info(f'Broker.place_order() Placing order for {order.shares} shares of {order.ticker_symbol}, {order.time_placed}')
        self.__orders.append(order)
    
    def cancel_order(self, order: Order) -> None:
        order.cancel()
    
    def process_orders(self, time: Optional[dt.datetime]=None) -> None:
        logger.info(f'Broker.process_orders() Processing {len(self.__orders)} orders at {time=}')
        for i,order in enumerate(list(self.__orders)):
            assert order.time_placed <= time, 'Order cannot be processed before it was placed'
            logger.info(f'Broker.process_orders() Propagating order #{i}...')
            position = self.__positions.get(order.ticker_symbol)
            if position is None:
                position = Position(self, order.ticker_symbol)
                self.__positions[order.ticker_symbol] = position
            position.process_order(order, time)
    
    def get_fee(self, shares: int, total_cents: int) -> int:
        logger.info(f'Broker.get_fee() Getting fee for {shares=} shares and {total_cents=} total cents ...')
        SEC = 0.0000278
        FINRA = 0.000166
        logger.info(f'... fee is {ceil(SEC*abs(total_cents)) + ceil(FINRA*abs(shares))}')
        return ceil(SEC*abs(total_cents)) + ceil(FINRA*abs(shares))

    def adjusted_price(self, shares: int, cents: int, high_cents: Optional[int]=sys.maxsize, low_cents: Optional[int]=0) -> int:
        logger.info(f'Broker.adjusted_price() Adjusting price for {shares=} shares and {cents=} cents ...')
        raw = cents*(1+copysign(self.__spread, shares))
        raw = min(raw, high_cents) if (shares>0) else max(raw,low_cents)
        logger.info(f'... adjusted price is {ceil(raw) if shares > 0 else floor(raw)}')
        return ceil(raw) if shares > 0 else floor(raw)

    def total_pl(self, current_time: Optional[dt.datetime]=None) -> int:
        return sum(position.total_pl(current_time) for position in self.__positions.values())
    
    def realized_pl(self, current_time: Optional[dt.datetime]=None) -> int:
        return sum(position.realized_pl(current_time) for position in self.__positions.values())
    
    def unrealized_pl(self, current_time: Optional[dt.datetime]=None) -> int:
        return sum(position.unrealized_pl(current_time) for position in self.__positions.values())
    
    def get_position(self, ticker_symbol: str) -> 'Position':
        position = self.__positions.get(ticker_symbol)
        if position is None:
            position = Position(self, ticker_symbol)
            self.__positions[ticker_symbol] = position
        return position

    def equity(self, time: Optional[dt.datetime]=None) -> int:
        return self.__cash + self.unrealized_pl(time)
    
    @property
    def orders(self) -> list[Order]:
        return self.__orders

    @property
    def cash(self) -> int:
        return self.__cash
    
    @cash.setter
    def cash(self, value: int) -> None:
        self.__cash = value

    @property
    def trade_on_close(self) -> bool:
        return self.__trade_on_close
    
    def __repr__(self) -> str:
        return f'Broker({self.__cash}, unrealized_pl={self.unrealized_pl()}, realized_pl={self.realized_pl()})'
    
class Trade:
    def __init__(self, broker: Broker, 
                 ticker_symbol: str, 
                 shares: int, 
                 entry_cents: int, 
                 entry_time: dt.datetime, 
                 exit_cents: Optional[int]=None, 
                 exit_time: Optional[dt.datetime]=None) -> None:
        logger.debug(f'Trade.__init__ Initializing Trade for {shares=} shares of {ticker_symbol=}')
        self.__broker = broker
        self.__ticker_symbol = ticker_symbol
        self.__shares = shares
        self.__entry_cents = entry_cents
        self.__exit_cents = exit_cents
        self.__entry_time = entry_time
        self.__exit_time = exit_time

    def pl(self, time: Optional[dt.datetime]=None) -> int:
        logger.info(f'Trade.pl() calculating pl for {self.__shares} shares of {self.__ticker_symbol} ...')
        logger.info(f'... Trade closed?: {self.is_closed()}')
        asset = AssetManager.get(self.__ticker_symbol)
        if not time:
            time = asset.latest_date()
        else:
            time = asset.prev_or_equal_date(time)
        high = asset.get_cents(time, 'High')
        low = asset.get_cents(time, 'Low')
        current_cents = self.__exit_cents if self.is_closed() else self.broker.adjusted_price(self.__shares,asset.get_cents(time), high, low)
        raw = self.shares * current_cents
        fee = self.__broker.get_fee(self.__shares, raw)
        logger.info(f'... Entry at {self.__entry_cents}, Exit at {current_cents}, Fee is {fee}, Shares is {self.__shares}')
        logger.info(f'... pl is {self.__shares * (current_cents - self.__entry_cents) - fee}')
        return self.__shares * (current_cents - self.__entry_cents) - fee

    def is_closed(self) -> bool:
        return self.__exit_cents is not None and self.__exit_time is not None

    def is_long(self) -> bool:
        return self.__shares > 0
    
    def is_short(self) -> bool:
        return self.__shares < 0

    @property
    def shares(self) -> int:
        return self.__shares
    
    @shares.setter
    def shares(self, value: int) -> None:
        self.__shares = value

    @property
    def entry_cents(self) -> int:
        return self.__entry_cents
    
    @property
    def exit_cents(self) -> Optional[int]:
        return self.__exit_cents

    @exit_cents.setter
    def exit_cents(self, value: int) -> None:
        assert self.__exit_cents is None, 'Trade already closed'
        logger.info(f'Trade for {self.__shares} shares of {self.__ticker_symbol} closed at price {value}')
        self.__exit_cents = value

    @property
    def entry_time(self) -> dt.datetime:
        return self.__entry_time

    @property
    def exit_time(self) -> Optional[dt.datetime]:
        return self.__exit_time

    @exit_time.setter
    def exit_time(self, value: dt.datetime) -> None:
        assert self.__exit_time is None, 'Trade already closed'
        logger.info(f'Trade for {self.__shares} shares of {self.__ticker_symbol} closed at time {value}')
        self.__exit_time = value
    
    @property
    def broker(self) -> Broker:
        return self.__broker
    
    def __repr__(self) -> str:
        return f'Trade({self.__ticker_symbol}, {self.__shares}, {self.__entry_cents=}, {self.__exit_cents=}, {self.__exit_time})'

class Position:
    '''
    A Position represents the current holdings of a particular Asset
    '''
    def __init__(self, broker: Broker, ticker_symbol: str, initial_shares: int = 0) -> None:
        logger.debug('Position.__init__ Initializing Position')
        self.__broker: Broker = broker
        self.__ticker_symbol = ticker_symbol
        self.__shares = initial_shares
        self.__trades: list[Trade] = []
        self.__closed_trades: list[Trade] = []
    
    def total_pl(self, current_time: Optional[dt.datetime]=None) -> int:
        return self.realized_pl(current_time) + self.unrealized_pl(current_time)
    
    def realized_pl(self, current_time: Optional[dt.datetime]=None) -> int:
        return sum(trade.pl(current_time) for trade in self.__closed_trades)
    
    def unrealized_pl(self, current_time: Optional[dt.datetime]=None) -> int:
        return sum(trade.pl(current_time) for trade in self.__trades)
    
    def process_order(self, order: Order, time: Optional[dt.datetime]=None) -> None:
        logger.info(f'Position.process_order() Processing order for {order.shares} shares of {order.ticker_symbol}')
        logger.info(f'... {order.type=}, {order.limit_cents=}, {order.stop_cents=}')
        asset = AssetManager.get(order.ticker_symbol)
        time = asset.prev_or_equal_date(time) if time else asset.latest_date()
        open_cents = asset.get_cents(time,'Open')
        high_cents = asset.get_cents(time,'High')
        low_cents = asset.get_cents(time,'Low')
        stop_cents = order.stop_cents
        limit_cents = order.limit_cents
        is_stop = order.is_stop()

        # If stop order, check to see if condition has been met
        if is_stop:
            logger.info(f'... order is stop, checking to see if hit')
            is_stop_hit = stop_cents <= high_cents if order.is_long() else low_cents <= stop_cents
            if not is_stop_hit:
                logger.info(f'... stop not hit, returning')
                return
            order.stop_cents = None
            order.type = ORDER_TYPE.LIMIT if order.is_limit() else ORDER_TYPE.MARKET
        
        if order.is_limit():
            logger.info(f'... order is limit, checking to see if hit')
            is_limit_hit = low_cents <= limit_cents if order.is_long() else limit_cents <= high_cents
            is_limit_hit_before_stop = (is_limit_hit and 
                                        is_stop and
                                        (limit_cents <= stop_cents if order.is_long() else stop_cents <= limit_cents))
            if not is_limit_hit or is_limit_hit_before_stop:
                logger.info(f'... limit not hit OR limit hit before stop, returning')
                return

            exec_price = (min(limit_cents, stop_cents or open_cents) if order.is_long() else 
                          max(limit_cents, stop_cents or open_cents))
        else:
            logger.info(f'... order is market')
            prev_time = asset.prev_date(time)
            prev_close = asset.get_cents(prev_time, 'Close')
            exec_price = prev_close if self.__broker.trade_on_close else open_cents
            if stop_cents:
                exec_price = max(exec_price, stop_cents) if order.is_long() else min(exec_price, stop_cents)
            exec_price = self.__broker.adjusted_price(order.shares, exec_price, high_cents, low_cents)
            time = prev_time if self.__broker.trade_on_close else time
        logger.info(f'... executing order at {exec_price}')
        need_shares = order.shares
        for trade in list(self.__trades):
            logger.info(f'... checking trade {trade} with {need_shares=}')
            if trade.is_long() == (need_shares > 0):
                continue
            logger.info(f'... found reverse-facing trade {trade}')
            if abs(trade.shares) > abs(need_shares):
                self.reduce_trade(trade, need_shares, time, exec_price)
                need_shares = 0
            else:
                self.close_trade(trade, time, exec_price)
                need_shares += trade.shares
            if need_shares == 0:
                break
        if need_shares != 0:
            self.open_trade(need_shares, exec_price, time)
        self.broker.orders.remove(order)
    
    def open_trade(self, shares: int, entry_cents: Optional[int]=None, entry_time: Optional[dt.datetime]=None) -> None:
        logger.info(f'Position.open_trade() Opening new trade for {shares} shares of {self.__ticker_symbol}, {entry_time}')
        entry_cents = entry_cents if entry_cents else AssetManager.get(self.__ticker_symbol).latest_cents()
        entry_time = AssetManager.get(self.__ticker_symbol).prev_or_equal_date(entry_time) if entry_time else AssetManager.get(self.__ticker_symbol).latest_date()
        trade = Trade(self.__broker, self.__ticker_symbol, shares, entry_cents, entry_time)
        self.update_shares(shares)
        self.__trades.append(trade)
    
    def reduce_trade(self, trade: Trade, amount: int, time: Optional[dt.datetime]=None, exit_cents: Optional[int]=None) -> None:
        logger.info(f'Position.reduce_trade() Reducing trade {trade} for {amount} shares of {self.__ticker_symbol}, {time}')
        assert trade.is_long() != (amount > 0)
        assert trade.shares + amount != 0
        assert (trade.shares+amount > 0) == trade.is_long()
        assert not trade.is_closed()
        exit_cents = exit_cents if exit_cents else AssetManager.get(self.__ticker_symbol).latest_cents()
        time = AssetManager.get(self.__ticker_symbol).prev_or_equal_date(time) if time else AssetManager.get(self.__ticker_symbol).latest_date()
        old_shares = trade.shares
        new_shares = old_shares + amount
        closed_trade = Trade(self.__broker, self.__ticker_symbol, -amount, trade.entry_cents, trade.entry_time)

        self.__trades.append(closed_trade)
        self.close_trade(closed_trade, time, exit_cents)
        trade.shares = new_shares
    
    def close_trade(self, trade: Trade, time: Optional[dt.datetime]=None, exit_cents: Optional[int]=None) -> None:
        logger.info(f'Position.close_trade() Closing trade {trade} for {self.__ticker_symbol}, {time}')
        exit_cents = exit_cents if exit_cents else AssetManager.get(self.__ticker_symbol).latest_cents()
        time = AssetManager.get(self.__ticker_symbol).prev_or_equal_date(time) if time else AssetManager.get(self.__ticker_symbol).latest_date()
        trade.exit_cents = exit_cents
        trade.exit_time = time
        self.update_shares(-trade.shares)
        self.__trades.remove(trade)
        self.__closed_trades.append(trade)

        # Update cash - pl includes fees
        pl = trade.pl()
        logger.info(f'... Adding {pl} from trade {trade} to cash')
        self.broker.cash += pl
    
    def update_shares(self, share_delta: int) -> None:
        self.__shares += share_delta

    @property
    def trades(self) -> list[Trade]:
        return self.__trades
    
    @property
    def closed_trades(self) -> list[Trade]:
        return self.__closed_trades

    @property
    def shares(self) -> int:
        return self.__shares

    @property
    def broker(self) -> Broker:
        return self.__broker
    
    @property
    def ticker_symbol(self) -> str:
        return self.__ticker_symbol
    
    def __repr__(self) -> str:
        return f'Position({self.__ticker_symbol}, {self.__shares})'
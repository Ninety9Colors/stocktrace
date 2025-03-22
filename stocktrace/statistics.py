import datetime as dt
import pandas as pd
from typing import Optional

from stocktrace.algorithm import Algorithm
from stocktrace.logger import Logger as logger
from stocktrace.backtest import Backtest
from stocktrace.trade_system import Broker, Trade, Position
from stocktrace.asset import Asset, AssetManager
from stocktrace.utils import TIMEZONE

def generate_statistics(closed_trades: list[Trade],
                        equity: pd.Series,
                        algorithm: Algorithm,
                        start_date: dt.datetime,
                        end_date: Optional[dt.datetime]=dt.datetime.now(tz=TIMEZONE),
                        alpha_ticker: str='^GSPC') -> pd.Series:
    result = pd.Series(dtype=object)

    alpha_asset = AssetManager.get(alpha_ticker)
    start = alpha_asset.prev_or_equal_date(start_date)
    end = alpha_asset.prev_or_equal_date(end_date)
    duration = end-start

    equity_peak = equity.iloc[0]
    equity_peak_date = equity.index[0]
    equity_final = equity.iloc[-1]

    return_pct = (equity_final-equity.iloc[0])/equity.iloc[0]
    bh_pct = (alpha_asset.get_cents(end_date)-alpha_asset.get_cents(start_date))/alpha_asset.get_cents(start_date)

    max_dd = 0
    max_dd_i = -1

    drawdowns = []
    in_drawdown = False
    # (start_date, start_equity, end_date, end_equity, min_date, min_equity)
    for i in range(1, len(equity.index)):
        if equity.iloc[i] >= equity_peak: # if reach a new high
            equity_peak = equity.iloc[i]
            equity_peak_date = equity.index[i]
            if in_drawdown:
                in_drawdown = False
                drawdowns[-1][2] = equity_peak_date
                drawdowns[-1][3] = equity_peak
        else:
            if not in_drawdown:
                in_drawdown = True
                drawdowns.append([equity_peak_date, equity_peak, None, None, equity.index[i], equity.iloc[i]])
            if equity.iloc[i] <= drawdowns[-1][5]:
                drawdowns[-1][5] = equity.iloc[i]
                drawdowns[-1][4] = equity.index[i]
            curr_dd = (equity.iloc[i]-equity_peak)/equity_peak
            if curr_dd < max_dd:
                max_dd = curr_dd
                max_dd_i = len(drawdowns)-1
    if in_drawdown:
        in_drawdown = False
        drawdowns[-1][2] = equity.index[-1]
        drawdowns[-1][3] = equity.iloc[-1]
    
    max_dd_duration = max(d[2]-d[0] for d in drawdowns)
    avg_dd = sum(((d[5]-d[1])/d[1] for d in drawdowns))/len(drawdowns)
    avg_dd_duration = sum((d[2]-d[0] for d in drawdowns),dt.timedelta(0))/len(drawdowns)
    max_dd_start = drawdowns[max_dd_i][0]
    max_dd_end = drawdowns[max_dd_i][2]

    max_trade_duration = dt.timedelta.min
    total_trades = 0
    total_trade_duration = dt.timedelta(0)
    total_trade_pct = 0
    best_trade = 0
    worst_trade = 0

    win_sum = 0
    loss_sum = 0
    num_wins = 0
    num_losses = 0
    for trade in closed_trades:
        curr_dur = trade.duration()
        total_trades += 1
        max_trade_duration = max(max_trade_duration, curr_dur)
        total_trade_duration += curr_dur

        pl_percent = trade.pl_fraction()
        total_trade_pct += pl_percent
        if pl_percent > 0:
            best_trade = max(best_trade, pl_percent)
            win_sum += pl_percent
            num_wins += 1
        elif pl_percent < 0:
            worst_trade = min(worst_trade, pl_percent)
            loss_sum += pl_percent
            num_losses += 1
    avg_win = win_sum/num_wins
    avg_loss = loss_sum/num_losses
    win_rate = num_wins/total_trades
    avg_trade_duration = total_trade_duration/total_trades
    avg_trade_pct = total_trade_pct/total_trades

    result.loc['Start'] = start
    result.loc['End'] = end
    result.loc['Duration'] = duration
    result.loc['Return %'] = return_pct*100
    result.loc[f'Buy and Hold Return % ({alpha_ticker})'] = bh_pct*100
    result.loc['Equity Final $'] = equity_final/100
    result.loc['Equity Peak $'] = equity_peak/100
    result.loc['Equity Peak Date'] = equity_peak_date
    result.loc['Win Rate %'] = win_rate*100
    result.loc['Best Trade %'] = best_trade*100
    result.loc['Worst Trade %'] = worst_trade*100
    result.loc['Avg Trade %'] = avg_trade_pct*100
    result.loc['Avg Win %'] = avg_win*100
    result.loc['Avg Loss %'] = avg_loss*100
    result.loc['Avg Trade Duration'] = avg_trade_duration
    result.loc['Max Trade Duration'] = max_trade_duration
    result.loc['Max Drawdown %'] = max_dd*100
    result.loc['Max Drawdown Begin'] = max_dd_start
    result.loc['Max Drawdown End'] = max_dd_end
    result.loc['Avg Drawdown %'] = avg_dd*100
    result.loc['Avg Drawdown Duration'] = avg_dd_duration
    result.loc['Max Drawdown Duration'] = max_dd_duration
    result.loc['Algorithm'] = algorithm

    return result
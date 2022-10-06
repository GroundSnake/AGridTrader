# coding=utf-8
# gm - strategy_id：d5498384-3f97-11ed-a875-b42e99f64ba9
# gm - token='3dcdec79cad272ab751050c0654ed4711a2fbdc2'
# Home_gm - strategy_id：83402db0-3f32-11ed-bcc8-4ae7da2ac5af
# Home_gm - token：3dcdec79cad272ab751050c0654ed4711a2fbdc2
from __future__ import print_function, absolute_import

import dill
from gm.api import *
from gm_utils import *

"""
os.environ['path_gm'] = ""  # 设置工作目录，未设置默认为初始化进程所在目录
"""


def init(context):
    stocks_price = {
        "SZSE.002621": 4.72,
    }
    if os.environ.get("path_gm", False):
        path_gm = os.environ.get("path_gm", False)
    else:
        path_gm = os.getcwd()
    if context.mode == MODE_BACKTEST:
        context.path_data = os.path.join(
            path_gm,
            f"data",
            r"backtest",
            f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
    else:
        context.path_data = os.path.join(path_gm, r"data", r"realtime")
    os.makedirs(context.path_data, exist_ok=True)
    file_log = os.path.join(context.path_data, "grid_trader.log")
    stream_handler = logging.StreamHandler(stream=None)
    stream_handler.setLevel(level=logging.INFO)  # set Console level
    file_handler = logging.FileHandler(filename=file_log, mode="a", encoding=None)
    file_handler.setLevel(level=logging.DEBUG)  # set file level
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        handlers=[stream_handler, file_handler],
    )

    symbols = stocks_price.keys()
    subscribe(symbols=symbols, frequency="tick")  # 订阅行情数据
    schedule(schedule_func=report_status, date_rule='1d', time_rule='09:31:00')  # 定时任务

    context.grid_traders = {}
    context.file_path_trader = {}
    for symbol in symbols:
        file_path_trader = os.path.join(context.path_data, f"{symbol}.cat")
        context.file_path_trader[symbol] = file_path_trader
        if os.path.exists(file_path_trader) and context.mode != MODE_BACKTEST:
            with open(file_path_trader, "rb") as file_trader:
                context.grid_traders[symbol] = dill.load(file_trader)
                logging.info(
                    f"[{context.grid_traders[symbol].symbol}] - init:Loaded Trader from {file_path_trader}"
                )

        else:
            with open(file_path_trader, "wb") as file_trader:
                price = stocks_price[symbol]
                context.grid_traders[symbol] = GridTrader(symbol=symbol, price=price)
                dill.dump(context.grid_traders[symbol], file_trader)
        logging.info(
            f"[{context.grid_traders[symbol].symbol}]- init: Trader 构建成功，最新时间：{context.now}"
        )


def on_tick(context, tick):
    order_side_map = {OrderSide_Buy: "买入", OrderSide_Sell: "卖出"}
    symbol = tick.symbol
    price = tick.price
    side = context.grid_traders[symbol].get_signal(price=price)
    volume = context.grid_traders[symbol].volume
    if side == OrderSide_Buy:
        order_volume(
            symbol=symbol,
            volume=volume,
            side=side,
            order_type=OrderType_Market,
            position_effect=PositionEffect_Open,
            price=price,
            order_duration=OrderDuration_Unknown,
            order_qualifier=OrderQualifier_BOC,
        )
        logging.debug(
            f"[{symbol}] - on_tick：方向：{order_side_map[side]} - 数量：{volume} -价格：{price} - Time：{context.now}")

    elif side == OrderSide_Sell:
        order_volume(
            symbol=symbol,
            volume=volume,
            side=side,
            order_type=OrderType_Market,
            position_effect=PositionEffect_Close,
            price=price,
            order_duration=OrderDuration_Unknown,
            order_qualifier=OrderQualifier_BOC,
        )
        logging.debug(
            f"[{symbol}] - on_tick：方向：{order_side_map[side]} - 数量：{volume} -价格：{price} - Time：{context.now}")


def on_execution_report(context, execrpt):
    symbol = execrpt.symbol
    side = execrpt.side
    price = execrpt.price
    volume = execrpt.volume
    signal_switch = context.grid_traders[symbol].signal_switch
    if not signal_switch:
        context.grid_traders[symbol].record(side=side, price=price)  # 记录交易数据
        file_path_trader = context.file_path_trader[symbol]
        with open(file_path_trader, "wb") as file_trader:
            dill.dump(context.grid_traders[symbol], file_trader)  # 将交易员当前状保存至硬盘
        logging.debug(f"[{symbol}] - on_execution_report：price:[{price}] - Time：{context.now}")
        if volume != context.grid_traders[symbol].volume:
            logging.debug(
                f"[{symbol}] -  on_execution_report：成交数量[{volume}]与委托数量[{context.grid_traders[symbol].volume}]不一致 - Time：{context.now}")


def on_error(context, code, info):
    print(f"on_execution_report：code:{code}, info:{info} - Time：{context.now}")
    # stop()





if __name__ == '__main__':
    '''
        strategy_id策略ID, 由系统生成
        filename文件名, 请与本文件名保持一致
        mode运行模式, 实时模式:MODE_LIVE回测模式:MODE_BACKTEST
        token绑定计算机的ID, 可在系统设置-密钥管理中生成
        backtest_start_time回测开始时间
        backtest_end_time回测结束时间
        backtest_adjust股票复权方式, 不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
        backtest_initial_cash回测初始资金
        backtest_commission_ratio回测佣金比例
        backtest_slippage_ratio回测滑点比例
        '''
    run(strategy_id='83402db0-3f32-11ed-bcc8-4ae7da2ac5af',
        filename='main.py',
        mode=MODE_LIVE,
        token='3dcdec79cad272ab751050c0654ed4711a2fbdc2',
        )


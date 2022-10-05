# -*- coding: utf-8 -*-
import datetime
import pandas
import logging
import os

from base.enum import *


class GridTrader:
    def __init__(self, symbol: str, price: float, volume: int = 100):
        """

        :param symbol: 股票gm代码 eg:'SHSE.600143'
        :param price: 前置研究确认后的启动中间价
        :param volume: 初始默认为100股。在程序初始化时：调用程序set_volume重新设置，运行期间不再改变。
        """
        # attribute:
        self.name = "GridTrader"  # Const Attribute
        self.symbol = symbol  # Const Attribute
        self.mid_price = price  # Const Attribute
        self.volume = volume  # 初级默认为100股。在程序初始化时：调用程序set_volume重新设置，运行期间不再改变。
        self.decline_rate = 0.05  # 股票下跌率，网格下限
        self.rise_rate = 0.05  # 股票上涨率，网格上限
        self.grid_count = 6  # 最大网格数
        self.mim_price = self.mid_price * (1 - self.grid_count * self.decline_rate)
        self.max_price = self.mid_price * (1 + self.grid_count * self.rise_rate)
        self.signal_switch = True
        self.price = None
        self.latest_transaction_price = None
        # data:
        ptc = ["symbol", "buy_datetime", "buy_price", "volume", "pnl", "pnl_ratio"]
        self.tick_position = pandas.DataFrame(columns=ptc)
        self.tick_position_row = -1  # tick_position的指针
        tran_columns = [
            "symbol",
            "buy_datetime",
            "buy_price",
            "volume",
            "sell_datetime",
            "sell_price",
            "hold",
            "pnl",
            "pnl_ratio",
        ]
        self.transaction = pandas.DataFrame(columns=tran_columns)
        self.transaction_row = -1  # transaction的指针

    def __repr__(self):
        return f"<{self.name} for {self.symbol}>"

    def record(self, side: int, price: float) -> bool:
        """get_signal()触发信号后，用成交的返回数据调用本方法
        :param side:未知[OrderSide_Unknown]，买入[OrderSide_Buy]，卖出[OrderSide_Sell]三选一。
        :param price:
        :return:记录成功返回Ture，记录失败返回False。
        """
        if self.signal_switch:  # [signal_switch]为Ture，本办法--不执行
            logging.error(f"[{self.symbol}] - Record：- No transaction signal")
            return False
        else:
            self.signal_switch = True  # 信号执行成功，打开信号监听
            logging.info(f"[{self.symbol}] - Record：- signal_switch = {self.signal_switch} ")

        if self.tick_position_row != self.tick_position.shape[0] - 1:
            logging.error(
                f"[{self.symbol}] -Record：- tick_position_row:{self.tick_position_row} != tick_position_shape:{self.tick_position.shape}"
            )
            return False
        elif self.transaction_row != self.transaction.shape[0] - 1:
            logging.error(
                f"[{self.symbol}] -Record：- transaction_row:{self.transaction_row} != transaction_shape:{self.transaction.shape}"
            )
            return False
        else:
            if side == OrderSide_Buy:
                self.latest_transaction_price = price
                self.tick_position_row += 1  # 指向将要新增记录位置，[tick_position_row]+1
                buy_datetime = datetime.datetime.now()
                self.tick_position.loc[self.tick_position_row] = [
                    self.symbol,
                    buy_datetime,
                    self.latest_transaction_price,
                    self.volume,
                    0,
                    0,
                ]
                logging.info(
                    f"[{self.symbol}] -Record：- Purchase {self.volume} at <{self.latest_transaction_price:6.2f}>"
                )
            elif side == OrderSide_Sell:
                if self.tick_position_row >= 0:
                    sell_datetime = datetime.datetime.now()
                    self.latest_transaction_price = price
                    hold = (
                        sell_datetime
                        - self.tick_position.loc[self.tick_position_row, "buy_datetime"]
                    )
                    pnl = (
                        self.latest_transaction_price
                        - self.tick_position.loc[self.tick_position_row, "buy_price"]
                    ) * self.tick_position.loc[self.tick_position_row, "volume"]
                    pnl_ratio = (
                        self.latest_transaction_price
                        / self.tick_position.loc[self.tick_position_row, "buy_price"]
                        - 1
                    ) * 100
                    self.transaction_row += 1  # 指向将要新增记录位置，[transaction_row]+1
                    self.transaction.loc[self.transaction_row] = [
                        self.tick_position.loc[self.tick_position_row, "symbol"],
                        self.tick_position.loc[self.tick_position_row, "buy_datetime"],
                        self.tick_position.loc[self.tick_position_row, "buy_price"],
                        self.tick_position.loc[self.tick_position_row, "volume"],
                        sell_datetime,
                        self.latest_transaction_price,
                        hold.days,
                        round(pnl, 2),
                        round(pnl_ratio, 2),
                    ]
                    logging.info(
                        f"[{self.symbol}] -Record：- Sell {self.volume} at <{self.latest_transaction_price:6.2f}>"
                    )
                    self.tick_position.drop(index=self.tick_position_row, inplace=True)
                    self.tick_position_row -= 1  # 删除了结交易记录，指向监控持仓点[tick_position_row]减1
                else:
                    logging.info(f"[{self.symbol}] - Record： -无持仓可卖！")
                    pass
            else:
                logging.debug(
                    f"[{self.symbol}] - Record：- record(side: int = {side},  price: float = {price})"
                )
                return False
            return True

    def update_tick_position(self, price: float) -> bool:
        """
        :param price:
        :return: DataFrame <tick_position> 为空，返回False
        """
        self.price = price
        if self.tick_position.empty:
            logging.debug(f"[{self.symbol}] - Update：- Tick position is empty")
            return False
        for index, data in self.tick_position.iterrows():
            pnl = (self.price - data["buy_price"]) * data["volume"]
            pnl_ratio = self.price / data["buy_price"] - 1
            self.tick_position.loc[index, "pnl"] = round(pnl, 2)
            self.tick_position.loc[index, "pnl_ratio"] = round(pnl_ratio, 4) * 100
        logging.debug(f"[{self.symbol}] - Update：- Update tick position")
        return True

    def get_signal(self, price: float) -> int:
        if self.signal_switch:  # [signal_switch]为Ture，本方法---执行
            self.price = price
            self.update_tick_position(price=self.price)
            if not self.latest_transaction_price:  # 首次建仓信号，不能用指针row，及share[0]
                logging.info(
                    f"[{self.symbol}] - Signal：买入 - [{self.price:.2f}] - [{self.volume}]股--首次建仓"
                )
                self.signal_switch = False
                return OrderSide_Buy
            elif self.price <= self.latest_transaction_price * (1 - self.decline_rate):
                if self.mim_price <= self.price <= self.max_price:
                    if self.tick_position.shape[0] < self.grid_count:
                        logging.info(
                            f"[{self.symbol}] - Signal：买入 [{self.price:.2f}] - [{self.volume}]股 - <{self.latest_transaction_price:.2f}>"
                        )
                        self.signal_switch = False
                        return OrderSide_Buy
                    else:
                        logging.debug(
                            f"[{self.symbol}] - Signal：分笔持仓达到{self.grid_count}笔，不再买入"
                        )
                        return OrderSide_Unknown
                else:
                    logging.debug(
                        f"[{self.symbol}] - Signal：虽然当前价[{self.price}]小于最近成交价[{self.latest_transaction_price}]的95%，但是不在买入范围区间[{self.mim_price}：{self.max_price}]"
                    )
                    return OrderSide_Unknown
            elif self.price >= self.latest_transaction_price * (1 + self.rise_rate):
                if self.tick_position.shape[0] > 0:  # 有持仓才能卖掉
                    logging.info(
                        f"[{self.symbol}] - Signal：卖出-[{self.symbol}] - [{self.price:.2f}] - [{self.volume}]股 - <{self.latest_transaction_price:.2f}>"
                    )
                    self.signal_switch = False
                    return OrderSide_Sell
                else:
                    logging.debug(f"[{self.symbol}] - Signal：无分笔持仓，不能卖出")
                    return OrderSide_Unknown
            elif self.latest_transaction_price * (1 - self.decline_rate) < self.price < self.latest_transaction_price * (1 + self.rise_rate):
                logging.debug(f"[{self.symbol}] - Signal：当前价：{price:.2f}在[{self.latest_transaction_price * (1 - self.decline_rate):.2f}：{self.latest_transaction_price * (1 + self.rise_rate):.2f}]")
                return OrderSide_Unknown
        else:
            logging.debug(f"[{self.symbol}] - Signal：signal_switch = False ")
            return OrderSide_Unknown

    def get_status(self, path: str):
        """
        :param path: 输出当前所有属性的数值到EXCEL文件，eg:'winter.xlsx'
        :return:
        """
        df_temp = pandas.DataFrame()
        df_temp.loc[0, "name"] = self.name
        df_temp.loc[0, "symbol"] = self.symbol
        df_temp.loc[0, "mid_price"] = self.mid_price
        df_temp.loc[0, "volume"] = self.volume
        df_temp.loc[0, "decline_rate"] = self.decline_rate
        df_temp.loc[0, "rise_rate"] = self.rise_rate
        df_temp.loc[0, "grid_count"] = self.grid_count
        df_temp.loc[0, "mim_price"] = self.mim_price
        df_temp.loc[0, "max_price"] = self.max_price
        df_temp.loc[0, "price"] = self.price
        df_temp.loc[0, "latest_transaction_price"] = self.latest_transaction_price
        df_temp.loc[0, "tick_position_row"] = self.tick_position_row
        df_temp.loc[0, "transaction_row"] = self.transaction_row
        with pandas.ExcelWriter(path=path, mode="w") as writer:
            if not self.tick_position.empty:
                self.tick_position.to_excel(
                    excel_writer=writer, sheet_name="tick_position"
                )
            if not self.transaction.empty:
                self.transaction.to_excel(excel_writer=writer, sheet_name="transaction")
            if not df_temp.empty:
                df_temp.to_excel(excel_writer=writer, sheet_name="attribute")
        logging.info(f"[{self.symbol}] - get_status：- {path} save")

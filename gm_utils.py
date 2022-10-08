# coding=utf-8
from object import *


def report_status(context):
    df_tick_position = pandas.DataFrame()
    df_transaction = pandas.DataFrame()
    for symbol in context.grid_traders.keys():
        df_temp_tick = context.grid_traders[symbol].tick_position
        if not df_temp_tick.empty:
            df_tick_position = pandas.concat(objs=[df_tick_position, df_temp_tick], ignore_index=True)
        df_temp_transaction = context.grid_traders[symbol].transaction
        if not df_temp_transaction.empty:
            df_transaction = pandas.concat(objs=[df_transaction, df_temp_transaction], ignore_index=True)
    if not df_tick_position.empty or not df_transaction.empty:
        pathname_tick_position = os.path.join(context.path_data, "grid_traders.xlsx")
        with pandas.ExcelWriter(path=pathname_tick_position, mode="w") as writer:
            if not df_tick_position.empty:
                df_tick_position.to_excel(excel_writer=writer, sheet_name="tick_position")
            else:
                logging.debug(f"report_status：<tick_position> is empty")
            if not df_transaction.empty:
                df_transaction.to_excel(excel_writer=writer, sheet_name="transaction")
            else:
                logging.debug(f"report_status：<transaction> is empty")
        logging.info(f"report_status：<grid_traders.xlsx> save - Time：{context.now}")
    else:
        logging.debug(f"report_status：<all> is empty")
        return False
    return True

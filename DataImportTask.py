import os
import shutil

import pandas as pd
from db import engine

import AppConfig


def import_from_xlsx(local_store):
    file_location = local_store[AppConfig.LAST_DATASET_UPLOADED]
    try:
        cols = pd.read_sql('select * from fund_nav limit 1', index_col='id', con=engine.engine).columns
        dat = pd.read_excel(file_location)
        dat.columns = cols
        dat.to_sql('fund_nav', if_exists='append', con=engine.engine, index=True, index_label='id')
        forward_fill_fund_nav_daily_table()
    finally:
        shutil.rmtree(os.path.dirname(file_location))


def forward_fill_fund_nav_daily_table():
    def reindex_group(group):
        date_range = pd.date_range(group.index.min(), group.index.max())
        return group.reindex(date_range).ffill()

    fund_nav = read_table_into_dataframe(table_name='fund_nav',
                                         index_col='id',
                                         coerce_float=True)

    fund_nav_daily = fund_nav.set_index('nav_date').groupby(['share_code', 'fund_code', 'share_type']) \
        .apply(reindex_group).reset_index([0, 1, 2], drop=True).reset_index(drop=False, names='nav_date')

    fund_nav_daily.loc[:, 'as_of_date'] = fund_nav_daily['price_in_fund']

    fund_nav_daily = fund_nav_daily.drop(columns=['price_in_fund']).merge(fund_nav[['nav_date',
                                                                                    'share_code',
                                                                                    'fund_code',
                                                                                    'share_type',
                                                                                    'price_in_fund']],
                                                                          how='left',
                                                                          on=['nav_date',
                                                                              'share_code',
                                                                              'fund_code',
                                                                              'share_type'])

    fund_nav_daily.to_sql('fund_nav_daily', if_exists='append', con=engine.engine, index=True, index_label='id')


def read_table_into_dataframe(table_name, index_col='id', coerce_float=True):
    return pd.read_sql_table(table_name=table_name,
                             index_col=index_col,
                             coerce_float=coerce_float,
                             con=engine.engine)


def read_sql_into_dataframe(sql, coerce_float=True):
    return pd.read_sql(sql,
                       coerce_float=coerce_float,
                       con=engine.engine)

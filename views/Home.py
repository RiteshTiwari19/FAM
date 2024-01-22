import dash_mantine_components as dmc
import numpy as np
from dash import html, callback, Output, no_update, Input, State
from dash.dcc import Interval
from dash.dcc import Graph
from dash_iconify import DashIconify
from db import engine
import plotly.express as px
import plotly.graph_objs as go

import DataImportTask


def get_home_page():
    fund_codes = DataImportTask \
        .read_sql_into_dataframe('select distinct fund_code from fund_nav_daily').to_numpy().flatten()
    return html.Div([
        dmc.Stack(children=[
            dmc.Group(children=[
                dmc.Group([
                    dmc.Badge(dmc.Text("FINECO"
                                       , size='lg'), variant='outline', color='gray',
                              radius='md', size='lg'),
                    dmc.Divider(orientation="vertical", style={"height": 35}),
                    dmc.Stack([
                        dmc.Text("ASSET", size='xs'),
                        dmc.Text("MANAGEMENT", size='xs')
                    ], style={'gap': '0px'}),
                ], style={'gap': '8px'}),
                dmc.Button(
                    "Import",
                    id="import-data-btn",
                    variant="filled",
                    leftIcon=DashIconify(icon="dashicons:database-import"),
                    className='zoom'
                ),
            ], position='apart'),
            dmc.Space(h=20),
            dmc.Group(
                children=[
                    dmc.Select(
                        id='fund_code_select',
                        label='Fund Code',
                        description='Select Fund',
                        data=fund_codes,
                        required=True,
                        searchable=True,
                        maxDropdownHeight=120,
                        disabled=False
                    ),
                    dmc.Select(
                        id='share_type_select',
                        label='Share Type',
                        description='Select share type',
                        data=[],
                        required=True,
                        searchable=True,
                        disabled=True,
                        clearable=True,
                        maxDropdownHeight=120,
                    ),
                    dmc.Button(
                        "Populate Dashboard",
                        variant='filled',
                        color='green',
                        id='populate_dashboard_btn',
                        disabled=True
                    )
                ],
                position='center', align='end'
            ),

            dmc.Space(h=10),
            dmc.Stack(
                children=[
                    html.Div(
                        dmc.Stack([
                            dmc.LoadingOverlay(
                                children=[
                                    dmc.Stack(
                                        children=[
                                            dmc.Skeleton(height='18em', width="100%", visible=True),
                                        ],
                                    )],
                                loaderProps={"variant": "dots", "color": "orange", "size": "xl"}
                            )
                        ], align='stretch'), id='plot-r1'),

                    html.Div(
                        dmc.Group(
                            children=[*get_loading_overlay()],
                            spacing='lg',
                            grow=True,
                            position='center',
                            id='plot-r2-group'
                        )
                    )
                ],
                align='stretch',
                id='plot_layout'
            ),

        ], align='stretch')
    ], style={'padding': '1.5em'})


def get_loading_overlay():
    return [html.Div(
        dmc.Stack([
            dmc.LoadingOverlay(
                children=[
                    dmc.Stack(
                        children=[
                            dmc.Skeleton(height='15em', width='100%', visible=True),
                        ],
                        align='stretch')],
                loaderProps={"variant": "dots", "color": "orange", "size": "xl"}
            )
        ], align='stretch'), id=f'plot-r2-f{i + 1}') for i in range(2)]


@callback(
    Output('populate_dashboard_btn', 'disabled'),
    Output('share_type_select', 'disabled'),
    Output('share_type_select', 'data'),
    Input('fund_code_select', 'value')
)
def get_share_types_for_fund_code(fund_code):
    if fund_code:
        return False, False, DataImportTask \
            .read_sql_into_dataframe(f"select distinct share_type from fund_nav_daily where fund_code = '{fund_code}'") \
            .to_numpy().flatten()
    else:
        return no_update, no_update, no_update


@callback(
    Output('plot-r1', 'children'),
    Output('plot-r2-group', 'children'),
    State('share_type_select', 'value'),
    State('fund_code_select', 'value'),
    Input('populate_dashboard_btn', 'n_clicks')
)
def get_daily_pct_change(share_type, fund_code, n_click):
    if not n_click or not share_type or not fund_code:
        return no_update, no_update, no_update

    data = DataImportTask.read_table_into_dataframe(table_name='fund_nav_daily') \
        .set_index('nav_date').sort_index()

    if len(data) == 0:
        return no_update, get_loading_overlay()
    else:
        daily_change = data[['share_code', 'fund_code', 'share_type', 'as_of_date']] \
            .groupby(['share_code', 'fund_code', 'share_type']).pct_change().fillna(0.)

        data['daily_pct_change'] = daily_change

        plot_data = data[(data['fund_code'] == fund_code) & (data['share_type'] == share_type)]

        # Fund Price Plot
        fund_price_plot = plot_data.copy(deep=True).reset_index()
        fund_price_plot_fig = px.area(data_frame=fund_price_plot, x='nav_date', y='price_in_share_currency')
        fund_price_plot_fig.update_layout(
            template='plotly_dark', xaxis_title="NAV Date", yaxis_title="Fund Price", showlegend=False
        )

        # Percent Change plot
        pct_change_plot_data = plot_data.copy(deep=True)
        pct_change_plot_data['clr'] = pct_change_plot_data['daily_pct_change'].apply(
            lambda x: 'green' if x >= 0 else 'red')

        mask = pct_change_plot_data['clr'] == 'green'
        pct_change_plot_data['pct_above'] = np.where(mask, pct_change_plot_data['daily_pct_change'], 0)
        pct_change_plot_data['pct_below'] = np.where(mask, 0, pct_change_plot_data['daily_pct_change'])
        pct_change_plot_data.reset_index(inplace=True)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=pct_change_plot_data['nav_date'], y=pct_change_plot_data['pct_above'], fill='tozeroy',
                       mode='none'))
        fig.add_trace(
            go.Scatter(x=pct_change_plot_data['nav_date'], y=pct_change_plot_data['pct_below'], fill='tozeroy',
                       mode='none'))

        fig.update_layout(template='plotly_dark', xaxis_title="NAV Date", yaxis_title="Daily Percentage Change")
        fig.update_layout(showlegend=False)

        pct_change_plot_data.set_index('nav_date', inplace=True)

        # 1 DAY %
        fig_1D = go.Figure()
        fig_1D.add_trace(go.Indicator(
            value=plot_data.loc[plot_data.index.max(), "price_in_share_currency"],
            mode="number",
            title={"text": f"ISIN: {plot_data['isin_code'].unique()[0]}<br><span style='font-size:0.8em;color:gray'>NAV Date: {plot_data.index.max().strftime('%m-%d-%Y')}</span><br><span style='font-size:0.8em;color:gray'>NAV Price</span>"},
            gauge={
                'axis': {'visible': False}},
            domain={'row': 0, 'column': 0}))

        fig_1D.add_trace(go.Indicator(
            mode="number+delta",
            title='1 Day %',
            value=pct_change_plot_data.sort_index(ascending=False).iloc[0]['daily_pct_change'],
            delta={'reference': pct_change_plot_data.sort_index(ascending=False).iloc[1]['daily_pct_change']},
            domain={'row': 0, 'column': 1}))


        fig_1D.update_layout(
            grid={'rows': 1, 'columns': 2, 'pattern': "independent"},
            template='plotly_dark')

        return Graph(figure=fund_price_plot_fig, id='fund_price_area_plot'), \
            dmc.Group(
                children=[
                    Graph(figure=fig, id='daily_pct_change_line_plot'),
                    dmc.Card(
                        children=[
                            dmc.Group(
                                [
                                    Graph(
                                        figure=fig_1D,
                                        responsive=True,
                                    )
                                ],
                                position='apart',
                                noWrap=False,
                                style={
                                    'gap': '7em'
                                }
                            )
                        ],
                        withBorder=True,
                        shadow="sm",
                        radius="md",
                        p='md',
                        style={"width": 350, "height": 450},
                    )
                ],
                grow=True
            )

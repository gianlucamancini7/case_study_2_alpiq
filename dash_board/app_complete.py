# Import required libraries
from datetime import date
import pandas as pd
import numpy as np
import json
import pathlib

# import dash app related packages
from flask import Flask
import dash
import dash_daq as daq
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objs as go
import copy

# import helper functions
from src.visualization.visualize_transactions_complete import executed_transactions_heatmap_summary, executed_transactions_time_series_dashboard
from src.data.welfare_complete import read_NTC_file, NTC_preparation, read_pw_file, pw_preparation

# Multi-dropdown options
app = dash.Dash(__name__)


# set layout
layout = dict(
    autosize=True,
    # automargin=True,
    margin=dict(
        l=30,
        r=30,
        b=20,
        t=40
    ),
    legend=dict(font=dict(size=10), orientation='h'),
    plot_bgcolor='white'
)

# helper functions


def df_to_plotly(df):

    diff = df.values.tolist()

    return {'z': diff,
            'x': df.columns.tolist(),
            'y': df.index.tolist()}


def format_thousands(number_string):

    n = 3
    if '-' in number_string:
        initial_ = '-'
        number_string = number_string.strip('-')
        rest = len(number_string.strip('-')) % 3
    else:
        initial_ = ''
        rest = len(number_string.strip('-')) % 3
    split_number = [number_string[:rest]] if rest != 0 else []
    split_number = split_number + [number_string[rest+i:rest+i+n]
                                   for i in range(0, len(number_string)-rest, n)]
    return initial_+','.join(split_number)


# load NTC
NTC = read_NTC_file(pathlib.Path(
    r"../data/external/NTC_DEandCH_2019.csv"))
NTC = NTC_preparation(NTC)

# load power limit data
power_lim = read_pw_file(
    pathlib.Path(
        r"../data/external/Hydro Generation up- downscale Potential_CH_2019.csv"))
power_lim = pw_preparation(power_lim)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id='aggregate_data'),
        html.Div(
            [
                html.Div(
                    [
                        html.H2(
                            'Studying the Lead Time Reduction on the Electricity Intraday Power Market ',

                        ),
                        html.P(
                            'An historical optimization study on the German-Swiss transactions prices, volumes, income, energy flows and carbon dioxide reduction in the 2019 German EPEX Intraday market data. The impact that the Swiss hydro flexible assets could have had on the 2019 German market transactions with 30 to 60 min lead time before delivery can be explored with the help of this tool.',
                        )
                    ],

                    className='twelve columns'
                )
            ],
            id="header",
            className='row',
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            'Choose Months',
                            className="control_label"
                        ),
                        dcc.RangeSlider(
                            id='year_slider',
                            min=0,
                            max=11,
                            marks={
                                0: 'Jan',
                                1: 'Feb',
                                2: 'Mar',
                                3: 'Apr',
                                4: 'May',
                                5: 'Jun',
                                6: 'Jul',
                                7: 'Aug',
                                8: 'Sep',
                                9: 'Oct',
                                10: 'Nov',
                                11: 'Dec',
                            },
                            value=[4, 6],
                            className="dcc_control"
                        ),
                        html.P(
                            'Vary the a posteriori transaction closing prices wrt to Hystorical Price on Monthly statistics',
                            className="control_label"
                        ),
                        dcc.Slider(
                            id='closing_price',
                            min=0,
                            max=10,
                            marks={
                                0: '0 %',
                                1: '10 %',
                                2: '20 %',
                                3: '30 %',
                                4: '40 %',
                                5: '50 %',
                                6: '60 %',
                                7: '70 %',
                                8: '80 %',
                                9: '90 %',
                                10: '100 %',

                            },
                            value=5,
                            className="dcc_control"
                        ),
                        html.P(
                            'Choose Day',
                            className="control_label"
                        ),
                        dcc.DatePickerSingle(
                            id='my-date-picker-single',
                            min_date_allowed=date(2019, 1, 1),
                            max_date_allowed=date(2019, 12, 31),
                            initial_visible_month=date(2019, 10, 1),
                            date=date(2019, 4, 25)
                        ),
                        html.P("Daily a Posteriori Traded Volumes Flows"),
                        dcc.Graph(id='piePlotVolume')
                    ],
                    className="pretty_container four columns"
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(
                                            "CH Suppliers Achievable Income [€]"),
                                        html.H6(
                                            id="ch_suppliers_income",
                                            className="info_text"
                                        )
                                    ],
                                    id="cC",
                                    className="pretty_container"
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            "DE Suppliers Achievable Income [€]"),
                                        html.H6(
                                            id="de_suppliers_income",
                                            className="info_text"
                                        )
                                    ],
                                    id="cCd",
                                    className="pretty_container"
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            "CH Buyers Achievable Income [€]"),
                                        html.H6(
                                            id="ch_buyers_income",
                                            className="info_text"
                                        )
                                    ],
                                    id="wch",
                                    className="pretty_container"
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            "DE Buyers Achievable Income [€]"),
                                        html.H6(
                                            id="de_buyers_income",
                                            className="info_text"
                                            # TO DO: format the output with commas toallow better reading of millions
                                        )
                                    ],
                                    id="wde",
                                    className="pretty_container"
                                )
                            ],
                            id="infoContainer",
                            className="row"
                        ),
                        # here a bar graph showing the additional total energy traded per month is shown: one for CH-DE flow and another for DE-CH flows
                        html.Div(
                            [html.H5("Monthly Statistics"),
                                dcc.RadioItems(
                                id='monthly_plot_type',
                                options=[
                                    {'label': 'Daily Volumes ',
                                     'value': 'daily_volume'},
                                    {'label': 'Daily Average Price',
                                     'value': 'daily_avg_price'},
                                    {'label': 'Daily Maximum Price ',
                                     'value': 'daily_max_price'}
                                ],
                                value='daily_volume',
                                labelStyle={
                                    'display': 'inline-block'},
                                className="dcc_control"
                            ),

                                dcc.Graph(
                                    id='energyTraded',
                            )
                            ],
                            id="countGraphContainer",
                            className="pretty_container"
                        )
                    ],
                    id="rightCol",
                    className="eight columns"
                )
            ],
            className="row"
        ),
        html.Div(
            [
                # heatmap comparison / net transfer capacity available and used / weekly average hydro prices
                html.Div(
                    [
                        html.H5(
                            "Hystorical and Aggregated a-Posteriori Hourly Price Differences "),
                        dcc.Graph(id='heatmap-comparison')
                    ],
                    className='pretty_container six columns',
                ),
                # daily price and moving average price variation comparison of before and after
                html.Div(
                    [
                        html.H5("Hystorical and a-Posteriori Price Variations"),
                        dcc.RadioItems(
                            id='which_effect_to_view_price',
                            options=[
                                {'label': 'CH-DE Flexibility Price Effect',
                                 'value': 'ch_de'},
                                {'label': 'DE-CH Flexibility Price Effect',
                                 'value': 'de_ch'},
                                {'label': 'Aggregated Effects',
                                 'value': 'both'}
                            ],
                            value='both',
                            labelStyle={
                                'display': 'inline-block'},
                            className="dcc_control"
                        ),
                        daq.ToggleSwitch(
                            id='smoothing-switch',
                            value=False,
                            label='View 1 Hour moving average values',
                            labelPosition='bottom'
                        ),
                        dcc.Graph(id='daily-time')
                    ],
                    className='pretty_container six columns',
                ),
            ],
            className='row'
        ),
        html.Div(
            [
                # plot of used net transfer capacity
                html.Div(
                    [
                        html.H5("Daily Transfer Capacity Usage"),
                        dcc.Graph(id='net-transfer-capacity')
                    ],
                    className='pretty_container seven columns',
                ),
                # plot of CO2 emission savings
                html.Div(
                    [
                        dcc.Markdown(
                            children='<h5>Monthly Statistic on CO<sub>2</sub> Reductions as Transaction Substitution from Hydro-Producer [tons CO<sub>2 eq</sub>]</h5>',
                            dangerously_allow_html=True),
                        dcc.Graph(id='co2')
                    ],
                    className='pretty_container seven columns',
                ),
            ],
            className='row'
        ),
    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)


# Helper functions


# Create callbacks
@app.callback(
    Output('piePlotVolume', 'figure'),
    Input('my-date-picker-single', 'date'))
def update_pieplot(date_value):

    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df_transactions = pd.read_csv(
            pathlib.Path(
                f'../data/processed/EPEX_spot_continous_complete_pipeline_2019_21-04-2021 21_54_04/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv')
        )

        data = [dict(
            type='pie',
            labels=['CH - DE Flows', 'DE - CH Flows'],
            values=[df_transactions['Executed Volume']
                    [df_transactions['match_binary_outcome_selling']
                        == 1].sum(), df_transactions['Executed Volume']
                    [df_transactions['match_binary_outcome_pumping'] == 1].sum()],
            name='CH-DE Daily Volume Exchnages',
            hole=0.5,
            hoverinfo="text+value+percent",
            textinfo="label+percent+name",
            autosize=False,
            height=20,
            width=10
        )]

        figure = dict(data=data, layout=layout)

    return figure


@app.callback(
    Output('net-transfer-capacity', 'figure'),
    Input('my-date-picker-single', 'date'))
def update_net_transfer_capacity(date_value):

    if date_value is not None:

        d_hours_CH_DE = dict(zip(range(24), [0]*24))
        d_hours_DE_CH = dict(zip(range(24), [0]*24))

        date_object = date.fromisoformat(date_value)
        NTC_selection = NTC[(NTC['start_time'].dt.day == date_object.day) & (
            NTC['start_time'].dt.month == date_object.month)]

        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        times_ntc = NTC_selection['start_time']

        # available transfer capacity
        ntc_gb_CH_DE = NTC_selection.groupby(times_ntc.dt.hour)[
            'CH to DE_Actual value (MW)']
        ntc_gb_DE_CH = NTC_selection.groupby(times_ntc.dt.hour)[
            'DE to CH_Actual value (MW)']

        # power limits
        power_lim_selection = power_lim[(power_lim['start_time'].dt.day == date_object.day) & (
            power_lim['start_time'].dt.month == date_object.month)]
        power_lim_selection['Upscale Potential [MW]'] = power_lim_selection['Upscale Potential [MW]'].astype(
            'float')
        power_lim_selection['Donwnscale Potential [MW]'] = power_lim_selection['Donwnscale Potential [MW]'].astype(
            'float')
        upscale_gb = power_lim_selection.groupby(power_lim_selection['start_time'].dt.hour)[
            'Upscale Potential [MW]']
        downscale_gb = power_lim_selection.groupby(power_lim_selection['start_time'].dt.hour)[
            'Donwnscale Potential [MW]']

        # load and read corresponding file
        df_transactions = pd.read_csv(
            pathlib.Path(
                f'../data/processed/EPEX_spot_continous_complete_pipeline_2019_21-04-2021 21_54_04/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv')
        )

        mask = df_transactions['match_binary_outcome_selling'] == 1
        df_transactions_filtered = df_transactions[mask]
        times_tr = pd.to_datetime(df_transactions_filtered['Delivery Start'])
        gb_ch_de = df_transactions_filtered.groupby(times_tr.dt.hour)[
            'Executed Volume']

        mask = df_transactions['match_binary_outcome_pumping'] == 1
        df_transactions_filtered = df_transactions[mask]
        times_tr = pd.to_datetime(df_transactions_filtered['Delivery Start'])
        gb_de_ch = df_transactions_filtered.groupby(times_tr.dt.hour)[
            'Executed Volume']

        d_hours_new_CH_DE = dict(
            zip(list(gb_ch_de.groups.keys()), gb_ch_de.sum()))
        d_hours_CH_DE.update(d_hours_new_CH_DE)

        d_hours_new_DE_CH = dict(
            zip(list(gb_de_ch.groups.keys()), gb_de_ch.sum()))
        d_hours_DE_CH.update(d_hours_new_DE_CH)

        figure = go.Figure(data=[go.Bar(name='CH-DE Used Available Transfer Capacity MW',
                                        x=list(d_hours_CH_DE.keys()),
                                        y=list(d_hours_CH_DE.values())),
                                 go.Bar(name='CH-DE Available Transfer Capacity MW',
                                        x=list(ntc_gb_CH_DE.groups.keys()),
                                        y=list(ntc_gb_CH_DE.mean())),
                                 go.Bar(name='DE-CH Used Available Transfer Capacity MW',
                                        x=list(d_hours_DE_CH.keys()),
                                        y=list(d_hours_DE_CH.values())),
                                 go.Bar(name='DE-CH Available Transfer Capacity MW',
                                        x=list(ntc_gb_DE_CH.groups.keys()),
                                        y=list(ntc_gb_DE_CH.mean())),
                                 go.Bar(name='Maximum Power Upscale Swiss Hydro-Producers MW',
                                        x=list(upscale_gb.groups.keys()),
                                        y=list(upscale_gb.mean())),
                                 go.Bar(name='Minimum Power Downscale Swiss Hydro-Producers MW',
                                        x=list(downscale_gb.groups.keys()),
                                        y=list(downscale_gb.mean()))
                                 ],
                           layout=layout)

        return figure


@ app.callback(
    Output('heatmap-comparison', 'figure'),
    Input('my-date-picker-single', 'date'))
def update_hetamap(date_value):

    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df_transactions = pd.read_csv(
            pathlib.Path(
                f'../data/processed/EPEX_spot_continous_complete_pipeline_2019_21-04-2021 21_54_04/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv')
        )

        daily_execution_price_stat, daily_execution_volume_stat, daily_execution_price_stat_marginal = executed_transactions_heatmap_summary(
            df_transactions, plot=False, return_updated_transactions=True)

        df_plot = (daily_execution_price_stat_marginal -
                   daily_execution_price_stat)/daily_execution_price_stat

        figure = go.Figure(data=go.Heatmap(df_to_plotly(df_plot),
                                           hovertemplate='Max ΔPrice wrt History: %{z:.2%}<br>Statistic: %{x}<br>Hour: %{y}<extra></extra>',
                                           colorbar={
            "title": 'Max ΔPrice wrt History', 'tickformat': '%'}
        )
        )

    return figure


@ app.callback(
    Output('daily-time', 'figure'),
    [Input('my-date-picker-single', 'date'),
     Input('which_effect_to_view_price', 'value'),
     Input('smoothing-switch', 'value'),
     ])
def update_output_table(date_value, which_effect, smoothing):

    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df_transactions = pd.read_csv(
            pathlib.Path(
                f'../data/processed/EPEX_spot_continous_complete_pipeline_2019_21-04-2021 21_54_04/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv')
        )
        if smoothing:
            time, output = executed_transactions_time_series_dashboard(
                df_transactions, which_effect=which_effect)

            outputseries = [0, 0]
            df_plotting = pd.DataFrame(
                data={'time': time, 'values': output[0]})
            outputseries[0] = df_plotting.set_index(
                'time')['values'].rolling('1H').mean()

            df_plotting = pd.DataFrame(
                data={'time': time, 'values': output[1]})
            outputseries[1] = df_plotting.set_index(
                'time')['values'].rolling('1H').mean()
        else:
            time, outputseries = executed_transactions_time_series_dashboard(
                df_transactions, which_effect=which_effect)

        data = [
            dict(
                type='scatter',
                mode='lines',
                name='Historical Execution Price €/MWh',
                x=time,
                y=outputseries[0],
                line=dict(
                    shape="spline",
                    smoothing=2,
                    width=1,
                    color='#fac1b7'
                )
            ),
            dict(
                type='scatter',
                mode='lines',
                name='A posteriori Execution Price €/MWh',
                x=time,
                y=outputseries[1],
                line=dict(
                    shape="spline",
                    smoothing=2,
                    width=1,
                    color='#849E68'
                )
            )
        ]

        figure = dict(data=data, layout=layout)

    return figure


@ app.callback(
    Output('co2', 'figure'),
    Input('year_slider', 'value'))
def update_co2(month_numbers):

    range_months = [month_numbers[0]+1, month_numbers[1]+1]

    df_summary = pd.read_csv(
        pathlib.Path(
            '../data/processed/summary_analysis_complete_window_interest_2019_21-04-2021 21_54_04/2019_21-04-2021 21_54_04_summary.csv'))
    time_ = pd.to_datetime(df_summary['time']).dt.month
    df_s = df_summary[(time_ >= range_months[0]) & (time_ <= range_months[1])]

    data = [
        dict(
            type='scatter',
            mode='lines',
            name='Historical CO2 Reduction [gCO2eq]',
            x=df_s['time'],
            y=df_s['Total Volume Traded CH-DE']*468.4*(10**3)/(10**6),
            line=dict(
                shape="spline",
                smoothing=2,
                width=1,
                color='#fac1b7'
            )
        )
    ]

    figure = dict(data=data, layout=layout)

    return figure


@ app.callback(
    [Output('energyTraded', 'figure'),
     Output('ch_suppliers_income', 'children'),
     Output('de_suppliers_income', 'children'),
     Output('ch_buyers_income', 'children'),
     Output('de_buyers_income', 'children')],
    [Input('year_slider', 'value'),
     Input('closing_price', 'value'),
     Input('monthly_plot_type', 'value')])
def update_main_graph(month_numbers, price, quantity):

    # which month to show
    range_months = [month_numbers[0]+1, month_numbers[1]+1]
    marks_price = {
        0: 0,
        1: 0.1,
        2: 0.2,
        3: 0.3,
        4: 0.4,
        5: 0.5,
        6: 0.6,
        7: 0.7,
        8: 0.8,
        9: 0.9,
        10: 1,
    }
    p = marks_price[price]

    # which quanity to show
    quantity_dict = {'daily_volume': ['Total Volume Traded', 'Total Volume Traded CH-DE', 'Total Volume Traded DE-CH'],
                     'daily_avg_price': ['Avg Historical Price', 'Avg a Posteriori Price'],
                     'daily_max_price': ['Max Historical Price', 'Max a Posteriori Price']}
    name_quantity_dict = {'daily_volume': ['Historical Volume Traded [MWh]', 'Potential Additional Volume Traded CH-DE [MWh]', 'Potential Additional Volume Traded DE-CH [MWh]'],
                          'daily_avg_price': ['Avg Daily Historical Price [€/MWh]', 'Avg Daily a Posteriori Price [€/MWh]'],
                          'daily_max_price': ['Max Daily Historical Price [€/MWh]', 'Max Daily a Posteriori Price [€/MWh]']}

    q = quantity_dict[quantity]
    name_q = name_quantity_dict[quantity]

    p_q = 0 if quantity == 'daily_volume' else p

    # load and read corresponding files
    df_summary = pd.read_csv(
        pathlib.Path(
            '../data/processed/summary_analysis_complete_window_interest_2019_21-04-2021 21_54_04/2019_21-04-2021 21_54_04_summary.csv'))
    time_ = pd.to_datetime(df_summary['time']).dt.month
    df_s = df_summary[(time_ >= range_months[0]) & (time_ <= range_months[1])]

    data = [
        dict(
            type='scatter',
            mode='lines',
            name=name_q[0],
            x=df_s['time'],
            y=df_s[q[0]],
            line=dict(
                shape="spline",
                smoothing=1,
                width=1,
                color='#fac1b7'
            ),
        ),
        dict(
            type='scatter',
            mode='lines',
            name=name_q[1],
            x=df_s['time'],
            y=df_s[q[1]]+p_q*(df_s[q[0]]-df_s[q[1]]),
            line=dict(
                shape="spline",
                smoothing=1,
                width=1,
                color='#849E68'
            ),
        ),
        dict(
            type='scatter',
            mode='lines',
            name=[] if quantity != 'daily_volume' else name_q[2],
            x=df_s['time'],
            y=[] if quantity != 'daily_volume' else df_s[q[2]],
            line=dict(
                shape="spline",
                smoothing=1,
                width=1,
                color='#0075B7'
            ),
        )]

    figure = dict(data=data, layout=layout)

    diff_welf_ch_de = df_s['CH-DE Revenue Max']-df_s['CH-DE Revenue Min']
    diff_welf_de_ch = df_s['DE-CH Revenue Min']-df_s['DE-CH Revenue Max']

    ch_suppliers = df_s['CH-DE Revenue Min'] + p*diff_welf_ch_de
    de_suppliers = -df_s['CH-DE Revenue Max'] + (1-p)*diff_welf_de_ch
    ch_buyers = p*diff_welf_de_ch
    de_buyers = (1-p)*diff_welf_ch_de

    return figure, format_thousands(str(ch_suppliers.sum()).split('.')[0]), format_thousands(str(de_suppliers.sum()).split('.')[0]), format_thousands(str(ch_buyers.sum()).split('.')[0]), format_thousands(str(de_buyers.sum()).split('.')[0])


# Main
if __name__ == '__main__':
    app.run_server(debug=False)

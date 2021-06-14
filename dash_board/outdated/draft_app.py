# import dash app related packages
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

# importlibraries
from datetime import date
import pandas as pd

# import helper functions
from src.data.helper_closed_transactions import read_epex_file, filter_lead_time, extract_transactions
from src.visualization.visualize_transactions import executed_transactions_time_series

from visualization_dash import generate_table


df_example = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

# set up style sheets
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# initiate app with style sheets
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    html.Label('Choose the day'),
    dcc.DatePickerSingle(
        id='my-date-picker-single',
        min_date_allowed=date(2019, 1, 1),
        max_date_allowed=date(2019, 10, 20),
        initial_visible_month=date(2019, 10, 1),
        date=date(2019, 10, 1)
    ),
    html.Div(id='output-container-date-picker-single'),
    html.Div(id='my-lob-table'),
    html.Div(id='my-transactions-table'),
    dcc.Graph(id='graph-time-series'),
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        id='year-slider',
        min=df_example['year'].min(),
        max=df_example['year'].max(),
        value=df_example['year'].min(),
        marks={str(year): str(year) for year in df_example['year'].unique()},
        step=None
    ),
    html.Div(children='''
        Dash: A web application framework for Python.
    ''')
])


@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    filtered_df = df_example[df_example.year == selected_year]

    fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
                     size="pop", color="continent", hover_name="country",
                     log_x=True, size_max=55)

    fig.update_layout(transition_duration=500)

    return fig


@app.callback(
    Output('output-container-date-picker-single', 'children'),
    Input('my-date-picker-single', 'date'))
def update_output(date_value):
    string_prefix = 'You have selected: '
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%B %d, %Y')
        return string_prefix + date_string


@app.callback(
    Output('my-lob-table', 'children'),
    Output('my-transactions-table', 'children'),
    Output('graph-time-series', 'figure'),
    Input('my-date-picker-single', 'date'))
def update_output_table(date_value):

    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df = read_epex_file(
            f"../data/external/EPEX_spot_continous_2019/DE Continuous Orders 2019-{month}/DE Continuous Orders 2019{month}{day}.csv",
            fast_load=False)

        # filter data
        df_filtered = filter_lead_time(df)

        # derive transactions
        pivoted, pivoted_levels = extract_transactions(
            df_filtered, new_data_type=False)
        time, outputseries = executed_transactions_time_series(
            pivoted_levels, plot=False, output_series='exec_price', rolling_time='1H', new_data_type=False)

        fig_time = px.line(pd.DataFrame(
            data={'time': time, 'exec_price': outputseries}), x="time", y="exec_price")

    return generate_table(df.head(20)), generate_table(pivoted_levels.head(20)), fig_time


if __name__ == '__main__':
    app.run_server(debug=True)

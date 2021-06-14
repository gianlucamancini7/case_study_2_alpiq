import dash
import dash_html_components as html
import dash_table as dt


def generate_table(dataframe, max_rows=10):
    """Function to draw tables in dash"""

    return dt.DataTable(
        data=dataframe.to_dict('rows'),
        columns=[{"name": i, "id": i, } for i in (dataframe.columns)]
        # columns=[{"name": i, "id": i, } for i in (dataframe.columns)]
    )

    # return html.Table([
    #     html.Thead(
    #         html.Tr([html.Th(col) for col in dataframe.columns])
    #     ),
    #     html.Tbody([
    #         html.Tr([
    #             html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
    #         ]) for i in range(min(len(dataframe), max_rows))
    #     ])
    # ])

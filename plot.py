import streamlit as st
from streamlit_elements import nivo
from streamlit_elements import mui, html

def plot_scatter(dataframe, x_variable, y_variable):
    """

    :param dataframe:
    :return: Plot
    """

def plot_metrics(dataframe, label, x_var):
    """

    :param dataframe: The dataframe that needs to be plotted
    :param label: The title of the chart
    :param x_var: The x variable or the metric that we want to be plotted
    :return: the plotted graph
    """
    x_var = x_var.split(",")[0]

    if len(dataframe) > 1:
        max_value = dataframe[x_var].max().round(2)
        min_value = dataframe[x_var].min().round(2)
        value = str(f"Ranges {min_value} to {max_value}")
    else:
        value = dataframe[x_var].round(2)

    print(value)

    return st.metric(label=label, value=value)

def create_bar_chart(data, x_var, y_var):

    data_chart = data.to_dict('records')
    key_x = data[x_var].unique()
    print(key_x)

    print(data_chart)

    nivo.Bar(
        data=data_chart,
        layout="vertical",
        keys=[y_var],
        indexBy=x_var,
        margin={ "top": 20, "right": 130, "bottom": 50, "left": 60 },
        padding={0.4},
        valueScale={ "type": 'linear' },
        indexScale={ "type": 'band', "round": "true" },
        colors={ "scheme": 'pastel1' },
        borderColor={
            "from": 'color',
            "modifiers": [
                [
                    'darker',
                    1.6
                ]
            ]
        },
        axisTop={"null"},
        labelSkipWidth={12},
        labelSkipHeight={12},
        labelTextColor={
            "from": 'color',
            "modifiers": [
                [
                    'darker',
                    1.6
                ]
            ]
        },
        legends=[
            {
                "dataFrom": 'keys',
                "anchor": 'top-right',
                "direction": 'column',
                "margin": { "left": 10 },
                "justify": "false",
                "translateX": 120,
                "translateY": 0,
                "itemsSpacing": 2,
                "itemWidth": 100,
                "itemHeight": 20,
                "itemDirection": 'left-to-right',
                "itemOpacity": 0.85,
                "symbolSize": 20,
                "effects": [
                    {
                        "on": 'hover',
                        "style": {
                            "itemOpacity": 1
                        }
                    }
                ]
            }
        ],
        role="application",
        ariaLabel="Nivo bar chart demo",
    )

def create_metric_chart(data, x_var, label):
    data_chart = data.to_dict('records')

    print(type(data_chart[0][x_var]))

    if 'float' in str(type(data_chart[0][x_var])):
        data_value = round(data_chart[0][x_var], 2)
    else:
        data_value = data_chart[0][x_var]

    with mui.Typography:
        html.div(
            html.p(label),
            html.p(data_value),
            css={
                "display": "block",
                "margin-top": "1em",
                "margin-bottom": "1em",
                "margin-left": "2em",
                "margin-right": "0em"
            }
        )


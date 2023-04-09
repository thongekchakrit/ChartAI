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

def create_bar_chart(data, x_var, y_var, hue_var, label):

    with mui.Typography:
        html.div(
            label,
            css={
                "display": "block",
                "margin-top": "1em",
                "margin-bottom": "1em",
                "margin-left": "2em",
                "margin-right": "0em"
            }
        )

    data_chart = data.to_dict('records')
    print("data chart", data_chart)
    print("x_var", x_var)
    print("y_var", y_var)
    print("hue_var", hue_var)

    nivo.Bar(
        data=data_chart,
        layout="vertical",
        keys=[y_var],
        indexBy=x_var,
        margin={"top": 20, "right": 130, "bottom": 100, "left": 60},
        padding={0.4},
        valueScale={"type": 'linear'},
        indexScale={"type": 'band', "round": "true"},
        colors={"scheme": 'pastel1'},
        borderColor={
            "from": 'color',
            "modifiers": [
                [
                    'darker',
                    1.6
                ]
            ]
        },
        axisBottom={
            'orient': 'bottom',
            "tickSize": 5,
            "tickPadding": 5,
            "tickRotation": 0,
            "legend": str(x_var),
            "legendPosition": 'middle',
            "legendOffset": 32
        },
        axisLeft={
            'orient': 'left',
            "tickSize": 5,
            "tickPadding": 5,
            "tickRotation": 0,
            "legend": str(y_var),
            "legendPosition": 'middle',
            "legendOffset": -40
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
        ariaLabel=label,
    )

def create_metric_chart(data, x_var, y_var, label):
    data_chart = data.to_dict('records')

    if x_var:
        x_var = x_var
    else:
        x_var = y_var

    if ('max' in str(data_chart)) & ('min' in str(data_chart)):
        min_value = None
        max_value = None

        for key, value in data_chart[0].items():
            if 'min' in key:
                min_value = round(value, 2)
            if 'max' in key:
                max_value = round(value, 2)

        data_value = str(f"Ranges {min_value} to {max_value}")

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
    else:

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
                    "margin-left": "1em",
                    "margin-right": "0em",
                    "flex": 1,
                    "minHeight": 0
                }
            )


def create_scatter_plot(data, x_var, y_var, hue_var, label):
    with st.spinner("Cooking the scatter plot now..."):
        print("Scatterplot: Starting data transformation")
        data_chart = data.to_dict('records')
        number_of_list = []
        for x in data_chart:
            number_of_list = number_of_list + [x[hue_var]]
        number_of_list = len(list(set(number_of_list)))
        list_of_dict = []
        counter = 0

        for x in data_chart:
            if list_of_dict:
                for y in list_of_dict:
                    if y['id'] == x[hue_var]:
                        y['data'].append({"x": x[x_var], "y": x[y_var]})
                    elif len(list(set([x for x in [k['id'] for k in list_of_dict]]))) < number_of_list:
                        list_of_dict = list_of_dict + [{'id': x[hue_var], 'data' : [{"x": x[x_var], "y": x[y_var]}]}]
            else:
                list_of_dict = list_of_dict + [{'id': x[hue_var], 'data' : [{"x": x[x_var], "y": x[y_var]}]}]
            print(counter)
            counter+=1

        with mui.Typography:
            html.div(
                label,
                css={
                    "display": "block",
                    "margin-top": "1em",
                    "margin-bottom": "1em",
                    "margin-left": "2em",
                    "margin-right": "0em"
                }
            )
        print("Scatterplot: Completed data transformation")

        nivo.ScatterPlot(
            data=list_of_dict,
            layout="vertical",
            xFormat=">-.2f",
            margin={"top": 20, "right": 130, "bottom": 100, "left": 60},
            padding={0.4},
            xScale={"type": 'linear', "min": 0, "max": 'auto'},
            yScale={"type": 'linear', "min": 0, "max": 'auto'},
            blendMode="multiply",
            indexScale={"type": 'band', "round": "true"},
            colors={"scheme": 'pastel1'},
            borderColor={
                "from": 'color',
                "modifiers": [
                    [
                        'darker',
                        1.6
                    ]
                ]
            },
            axisBottom={
                'orient': 'bottom',
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": str(x_var),
                "legendPosition": 'middle',
                "legendOffset": 32
            },
            axisLeft={
                'orient': 'left',
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": str(y_var),
                "legendPosition": 'middle',
                "legendOffset": -40
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
            ariaLabel=label
        )
        print("Scatterplot: Plotted")


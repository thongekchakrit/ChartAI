import streamlit as st
import random
from streamlit_elements import nivo
from streamlit_elements import mui, html

def create_bar_chart(data, x_var, y_var, hue_var, title):

    """
    :param data: The dataframe that needs to be plotted
    :param title: The title of the chart
    :param x_var: The x numerical variable or the metric that we want to be plotted
    :param x_var: The y numerical variable is the metric that we want to measure
    :param hue_var: The hue variable is the categorical data that we would like to plot
    :return: bar chart
    """

    if (x_var != 'None') & (y_var != 'None'):

        if hue_var == 'None':
            hue_var = x_var

        hue_var = hue_var.split(",")[0]
        print("hue_var", hue_var)
        x_var = x_var.split(",")[0]
        y_var = y_var.split(",")[0]

        with mui.Typography:
            html.div(
                title,
                css={
                    "display": "block",
                    "margin-top": "1em",
                    "margin-bottom": "1em",
                    "margin-left": "1em",
                    "margin-right": "0em",
                    "font-weight": "bold"
                }
            )
        if len([x for x in data[x_var].unique()]) > 10:
            x_tick_rotation = 25
            bottom_padding = 150
            legendOffset = 65
        else:
            x_tick_rotation = 0
            bottom_padding = 100
            legendOffset = 32
        data_chart = data.to_dict('records')
        # print("x_var", x_var)
        # print("y_var", y_var)
        # print("hue_var", hue_var)
        print("Data", data_chart)

        nivo.Bar(
            data=data_chart,
            layout="vertical",
            keys=[y_var],
            indexBy=x_var,
            margin={"top": 20, "right": 130, "bottom": bottom_padding, "left": 60},
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
                "tickRotation": x_tick_rotation,
                "legend": str(x_var),
                "legendPosition": 'middle',
                "legendOffset": legendOffset
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
            ariaLabel=title,
        )



def create_metric_chart(data, x_var, y_var, title):

    """
    :param dataframe: The dataframe that needs to be plotted
    :param label: The title of the chart
    :param x_var: The x variable or the metric that we want to be plotted
    :return: the plotted graph
    """

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
                html.p(title),
                css={
                    "display": "block",
                    "margin-top": "1em",
                    "margin-bottom": "1em",
                    "margin-left": "2em",
                    "margin-right": "0em",
                    "font-weight": "bold"
                })
    else:

        if 'float' in str(type(data_chart[0][x_var])):
            data_value = round(data_chart[0][x_var], 2)
        else:
            data_value = data_chart[0][x_var]

        with mui.Typography:
            html.div(
                html.p(title),
                css={
                    "display": "block",
                    "margin-top": "1em",
                    "margin-bottom": "1em",
                    "margin-left": "1em",
                    "margin-right": "0em",
                    "flex": 1,
                    "minHeight": 0,
                    "font-weight": "bold"
                }
            )
            html.div(
                html.p(data_value),
                css={
                    "display": "block",
                    "margin-top": "1em",
                    "margin-bottom": "1em",
                    "margin-right": "0em",
                    "flex": 1,
                    "minHeight": 0,
                    "font-weight": "900",
                    "font-size": "x-large",
                    "text-align": "center"
                }
            )

def create_scatter_plot(data, x_var, y_var, hue_var, title):

    """
    :param data: The dataframe that needs to be plotted
    :param title: The title of the chart
    :param x_var: The x numerical variable or the metric that we want to be plotted
    :param x_var: The y numerical variable is the metric that we want to measure
    :param hue_var: The hue variable is the categorical data that we would like to plot
    :return: scatter plot
    """

    if hue_var:
        hue_var = hue_var.split(",")[0]
    if x_var:
        x_var = x_var.split(",")[0]
    if y_var:
        y_var = y_var.split(",")[0]

    if hue_var:
        with st.spinner("Cooking the scatter plot now..."):
            # print("Scatterplot: Starting data transformation")
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
                    title,
                    css={
                        "display": "block",
                        "margin-top": "1em",
                        "margin-bottom": "1em",
                        "margin-left": "1em",
                        "margin-right": "0em",
                        "font-weight": "bold"
                    }
                )
            # print("Scatterplot: Completed data transformation")

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
                        "legend": str(hue_var),
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
                ariaLabel=title
            )
    else:
        raise


def create_swarm_plot(data, x_var, y_var, hue_var, title):

    """
    :param data: The dataframe that needs to be plotted
    :param title: The title of the chart
    :param x_var: The x numerical variable or the metric that we want to be plotted
    :param x_var: The y numerical variable is the metric that we want to measure
    :param hue_var: The hue variable is the categorical data that we would like to plot
    :return: swarm plot
    """
    if hue_var:
        list_hue_var= [x for x in data[hue_var].unique()]
        data_to_plot = data.reset_index().rename(columns={'index': 'id', hue_var: 'group'})[['id', 'group', y_var, x_var]].to_dict('records')
        minimum_y = round(data[y_var].min())
        max_y = round(data[y_var].max())
        min_x = round(data[x_var].min())
        max_x = round(data[x_var].max())

        with mui.Typography:
            html.div(
                title,
                css={
                    "display": "block",
                    "margin-top": "1em",
                    "margin-bottom": "1em",
                    "margin-left": "1em",
                    "margin-right": "0em",
                    "font-weight": "bold"
                }
            )

        nivo.SwarmPlot(
        data=data_to_plot,
        groups=list_hue_var,
        identity="id",
        value=y_var,
        valueFormat=".2f",
        valueScale={ "type": 'linear', "min": minimum_y, "max": max_y, "reverse": False },
        size={
            "key": x_var,
            "values": [
                min_x,
                max_x
            ],
            "sizes": [
                6,
                21
            ]
        },
        forceStrength=4,
            borderColor={
                "from": 'color',
                "modifiers": [
                    [
                        'darker',
                        0.6
                    ],
                    [
                        'opacity',
                        0.5
                    ]
                ]
            },
        margin={ "top": 80, "right": 100, "bottom": 80, "left": 100 },
        axisTop={
            "orient": 'top',
            "tickSize": 10,
            "tickPadding": 5,
            "tickRotation": 0,
            "legend": f'{hue_var} if vertical, {y_var} if horizontal, {x_var} if size',
            "legendPosition": 'middle',
            "legendOffset": -46
        },
        axisRight={
            "orient": 'right',
            "tickSize": 10,
            "tickPadding": 5,
            "tickRotation": 0,
            "legend": f'{y_var} if vertical, {hue_var} if horizontal, {x_var} if size',
            "legendPosition": 'middle',
            "legendOffset": 76
        },
        axisBottom={
            "orient": 'bottom',
            "tickSize": 10,
            "tickPadding": 5,
            "tickRotation": 0,
            "legend": f'{hue_var} if vertical, price if horizontal, {x_var} if size',
            "legendPosition": 'middle',
            "legendOffset": 46
        },
        axisLeft={
            "orient": 'left',
            "tickSize": 10,
            "tickPadding": 5,
            "tickRotation": 0,
            "legend": f'{y_var} if vertical, {hue_var} if horizontal, {x_var} if size',
            "legendPosition": 'middle',
            "legendOffset": -76
        })
    else:
        raise

def create_box_plot(data, x_var, y_var, hue_var, title):

    """
    :param data: The dataframe that needs to be plotted
    :param title: The title of the chart
    :param x_var: The x numerical variable or the metric that we want to be plotted
    :param x_var: The y numerical variable is the metric that we want to measure
    :param hue_var: The hue variable is the categorical data that we would like to plot
    :return: swarm plot
    """
    if hue_var:
        list_hue_var= [x for x in data[hue_var].unique()]
        data_to_plot = data.reset_index().rename(columns={'index': 'id', hue_var: 'group'})[['id', 'group', y_var, x_var]].to_dict('records')
        minimum_y = round(data[y_var].min())
        max_y = round(data[y_var].max())
        min_x = round(data[x_var].min())
        max_x = round(data[x_var].max())

        with mui.Typography:
            html.div(
                title,
                css={
                    "display": "block",
                    "margin-top": "1em",
                    "margin-bottom": "1em",
                    "margin-left": "1em",
                    "margin-right": "0em",
                    "font-weight": "bold"
                }
            )

        nivo.BoxPlot(
            data=data_to_plot,
            groups=list_hue_var,
            margin={"top": 60, "right": 140, "bottom": 60, "left": 60 },
            minValue=minimum_y,
            maxValue=max_y,
            padding=0.12,
            enableGridX=True,
            axisTop={
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": '',
                "legendPosition": 'middle',
                "legendOffset": 36
            },
            axisRight={
                "orient": 'right',
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": f'',
                "legendPosition": 'middle',
                "legendOffset": 0
            },
            axisBottom={
                "orient": 'bottom',
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": f'',
                "legendPosition": 'middle',
                "legendOffset": 32
            },
            axisLeft={
                "orient": 'left',
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": f'',
                "legendPosition": 'middle',
                "legendOffset": -76
            })
    else:
        raise

def create_pie_chart(data_to_plot,x_var, y_var, hue_var, title):

    lst = []

    if x_var == 'None':
        x_var = hue_var
    for x in range(0, len(data_to_plot)):
        lst = lst + [f"hsl({random.randint(10, 255)}, 70%, 50%)"]

    df_new= data_to_plot.reset_index().rename(columns={'index': 'id', y_var: 'value'})
    df_new['id'] = df_new[x_var]
    df_new['label'] = df_new[x_var]
    df_new['color'] = lst
    data_to_plot_json = df_new.to_dict('records')

    print(data_to_plot_json)

    with mui.Typography:
        html.div(
            title,
            css={
                "display": "block",
                "margin-top": "1em",
                "margin-bottom": "1em",
                "margin-left": "1em",
                "margin-right": "0em",
                "font-weight": "bold"
            }
        )

    nivo.Pie(
        data=data_to_plot_json,
        margin={"top": 20, "right": 40, "bottom": 85, "left": 40},
        innerRadius=0.5,
        padAngle=0.7,
        cornerRadius=3,
        activeOuterRadiusOffset=8,
        borderWidth=1,
        borderColor={
            "from": 'color',
            "modifiers": [
                [
                    'darker',
                    0.2
                ]
            ]
        },
        arcLinkLabelsSkipAngle=10,
        arcLinkLabelsTextColor="#333333",
        arcLinkLabelsThickness=2,
        arcLinkLabelsColor={"from": 'color'},
        arcLabelsSkipAngle=10,
        arcLabelsTextColor={
            "from": 'color',
            "modifiers": [
                [
                    'darker',
                    2
                ]
            ]
        }
    )

def create_line_chart(data_to_plot, x_var, y_var, hue_var, title):

    # Sort the column X
    if hue_var:
        hue_var = hue_var.split(",")[0]
    if x_var:
        x_var = x_var.split(",")[0]
        # x_var = 'month'
    if y_var:
        y_var = y_var.split(",")[0]

    data_to_plot = data_to_plot.sort_values(by=[x_var])

    for col, dtype in data_to_plot.dtypes.items():
        if 'datetime' in str(dtype):
            data_to_plot[col] = data_to_plot[col].dt.strftime('%Y-%m-%d')

    if hue_var != 'None':
        list_hue_var= [x for x in data_to_plot[hue_var].unique()]
        lst_of_dict = []

        for x in list_hue_var:
            lst_of_dict = lst_of_dict + [{
                "id": x,
                "color": f"hsl({random.randint(10, 255)}, 70%, 50%)",
                "data": data_to_plot[data_to_plot[hue_var] == x].rename(columns={x_var: 'x', y_var: 'y'}).to_dict('records')
            }]

        data_to_plot = lst_of_dict
    else:
        random_color = f"hsl({random.randint(10, 255)}, 70%, 50%)"
        data_to_plot = [{
            "id": y_var,
            "color": random_color,
            "data": data_to_plot.rename(columns={x_var: 'x', y_var: 'y'}).to_dict('records')
        }]

    print("Line plot: ", data_to_plot)

    with mui.Typography:
        html.div(
            title,
            css={
                "display": "block",
                "margin-top": "1em",
                "margin-bottom": "1em",
                "margin-left": "1em",
                "margin-right": "0em",
                "font-weight": "bold"
            }
        )

    nivo.Line(
        data=data_to_plot,
        margin={ "top": 20, "right": 120, "bottom": 130, "left": 60 },
        xScale={ "type": 'point' },
        yScale={
        "type": 'linear',
        "min": 'auto',
        "max": 'auto'},
        yFormat=" >-.2f",
        axisBottom={
        "orient": 'bottom',
        "tickSize": 1,
        "tickPadding": 5,
        "tickRotation": 45,
        "legend": x_var,
        "legendOffset": 60,
        "legendPosition": 'middle'
        },
        axisLeft={
            "orient": 'left',
            "tickSize": 5,
            "tickPadding": 5,
            "tickRotation": 0,
            "legend": 'count',
            "legendOffset": -40,
            "legendPosition": 'middle'
        },
        pointSize=6,
        pointColor={ "theme": 'background' },
        pointBorderWidth=2,
        pointBorderColor={"from": 'serieColor' },
        pointLabelYOffset=-6,
        useMesh="true",
        legends=[
            {
                "anchor": 'top-right',
                "direction": 'column',
                "justify": "false",
                "translateX": 100,
                "translateY": 0,
                "itemsSpacing": 0,
                "itemDirection": 'left-to-right',
                "itemWidth": 90,
                "itemHeight": 20,
                "itemOpacity": 0.75,
                "symbolSize": 12,
                "symbolShape": 'circle',
                "symbolBorderColor": 'rgba(0, 0, 0, .5)',
                "effects": [
                    {
                        "on": 'hover',
                        "style": {
                            "itemBackground": 'rgba(0, 0, 0, .03)',
                            "itemOpacity": 1
                        }
                    }
                ]
            }
        ]
    )


def create_error_plot():
    with mui.Typography:
        html.div(
            html.p("Error"),
            css={
                "display": "block",
                "margin-top": "1em",
                "margin-bottom": "1em",
                "margin-right": "0em",
                "flex": 1,
                "minHeight": 0,
                "font-weight": "900",
                "font-size": "x-large",
                "text-align": "center"
            }
        )


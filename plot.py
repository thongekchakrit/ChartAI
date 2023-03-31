import plotly
import streamlit as st
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


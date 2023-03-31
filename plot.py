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

    return st.metric(label=label, value=dataframe[x_var].round(2), use_container_width=True)


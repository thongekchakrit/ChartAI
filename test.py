import streamlit as st
import pandas as pd
import altair as alt

st.title("Graph Plotting App")

# Get user input for graph data
data_file = st.file_uploader("Upload a CSV file", type=["csv"])

if data_file is not None:
    data = pd.read_csv(data_file)
    st.write("Data preview:")
    st.write(data.head())

    # Function to filter data
    def filter_data(df):
        filtered_df = df
        column_names = df.columns
        for column in column_names:
            if df[column].dtype == "O":
                continue
            if pd.api.types.is_datetime64_any_dtype(df[column].dtype):
                date_range = st.sidebar.date_input(f"Select {column} range", [df[column].min(), df[column].max()])
                start_date, end_date = date_range
                filtered_df = filtered_df[(filtered_df[column] >= start_date) & (filtered_df[column] <= end_date)]
            else:
                min_val = st.sidebar.number_input(f"Min {column}", value=df[column].min())
                max_val = st.sidebar.number_input(f"Max {column}", value=df[column].max())
                if min_val > max_val:
                    st.sidebar.error("Please enter a valid range")
                    continue
                filtered_df = filtered_df[(filtered_df[column] >= min_val) & (filtered_df[column] <= max_val)]
        return filtered_df

    # Get user input for graph type
    graph_type = st.selectbox("Select graph type", ["Line", "Bar", "Scatter"])

    # Filter data
    data = filter_data(data)

    # Plot graph based on user input
    if graph_type == "Line":
        chart = alt.Chart(data).mark_line().encode(
            x=st.selectbox("X-axis", list(data.columns)),
            y=st.selectbox("Y-axis", list(data.columns)),
            color=st.selectbox("Color", list(data.columns)),
        ).interactive()

    elif graph_type == "Bar":
        chart = alt.Chart(data).mark_bar().encode(
            x=st.selectbox("X-axis", list(data.columns)),
            y=st.selectbox("Y-axis", list(data.columns)),
            color=st.selectbox("Color", list(data.columns)),
        ).interactive()

    else:
        chart = alt.Chart(data).mark_point().encode(
            x=st.selectbox("X-axis", list(data.columns)),
            y=st.selectbox("Y-axis", list(data.columns)),
            color=st.selectbox("Color", list(data.columns)),
        ).interactive()

    st.altair_chart(chart, use_container_width=True)

import streamlit as st
import pandas as pd
import gpt3
import csv
import numpy as np
import os

st.set_page_config(page_title="Automated Data Analysis")

st.write("## Data Analytics AI")
st.write(
    "Uploading a csv, ask a question and gain insights from your data."
)

DATA_URL = ('dataset/File_2_ID_2015_Domains_of_deprivation.csv')

UPLOADED_FILE = st.file_uploader("Choose a file")
GPT_SECRETS = st.secrets["gpt_secret"]
gpt3.openai.api_key = GPT_SECRETS


@st.cache_data
def load_data(nrows):
    if UPLOADED_FILE is not None:
        data = pd.read_csv(UPLOADED_FILE, nrows=nrows)
        lowercase = lambda x: str(x).lower()
        data.rename(lowercase, axis='columns', inplace=True)
        with open(UPLOADED_FILE) as file:
            content = file.readlines()
            header = content[:1]
            rows = content[1:nrows]
    else:
        st.warning("Please upload a csv file, using default dataset...")
        data = pd.read_csv(DATA_URL, nrows=nrows)
        lowercase = lambda x: str(x).lower()
        data.rename(lowercase, axis='columns', inplace=True)
        with open(DATA_URL) as file:
            content = file.readlines()
            header = content[:1]
            rows = content[1:nrows]
    return data, header, rows

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')
# Load 10,000 rows of data into the dataframe.
data, header, rows = load_data(500)
# Notify the reader that the data was successfully loaded.

# Inspecting raw data
st.subheader('Raw data')
st.write(data)

st.markdown(f"### Overview of the data.")
with st.spinner(text="In progress..."):
    prompt = f"Given the csv file with headers: {header[0]} describe the dataset"
    response = gpt3.gpt_promt(prompt)
    st.caption(response['content'])

st.subheader('Automated Visualizations')
st.text('Ask questions below and let AI do the visualization for you')

text_input = st.text_input(
    "Enter questions 👇"
)

st.markdown(f"User question: {text_input}")


# Hidding footer
hide_default_format = """
       <style>
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)
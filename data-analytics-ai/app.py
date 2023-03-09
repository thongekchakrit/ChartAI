import streamlit as st
import pandas as pd
import gpt3
import duckdb
import plotly


st.set_page_config(page_title="Automated Data Analysis")

st.write("## Data Analytics AI")
st.write(
    "Uploading a csv, ask a question and gain insights from your data."
)

DATA_URL = ('File_2_ID_2015_Domains_of_deprivation.csv')

UPLOADED_FILE = st.file_uploader("Choose a file")
GPT_SECRETS = st.secrets["gpt_secret"]
gpt3.openai.api_key = GPT_SECRETS

# Hiding footer
hide_default_format = """
       <style>
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

@st.cache_resource
def load_data(UPLOADED_FILE):
    if UPLOADED_FILE is not None:
        data = pd.read_csv(UPLOADED_FILE)
        lowercase = lambda x: str(x).lower()
        data.rename(lowercase, axis='columns', inplace=True)
    else:
        st.warning("Please upload a csv file, using default dataset...")
        data = pd.read_csv(DATA_URL, nrows=5)
        lowercase = lambda x: str(x).lower()
        data.rename(lowercase, axis='columns', inplace=True)

    data_random_sample = data.sample(frac=0.05)
    rows = data_random_sample.values.tolist()
    header = data_random_sample.columns.tolist()
    sample_data_overview = header + rows[:10]
    return data, sample_data_overview

@st.cache_data
def get_data_overview(header):
    with st.spinner(text="In progress..."):
        prompt = f"Given the csv file with headers: {header} describe what each column means and what the dataset can be used for"
        response = gpt3.gpt_promt(prompt)
        st.caption(response['content'])
    if 'question_dict' not in st.session_state:
        st.session_state['question_dict'] = {}
@st.cache_data
def add_new_row(sample_data_overview, new_question):
    prompt = f"Given the csv file sample data with headers: {sample_data_overview}, write a sql script with given dataset columns to get '{new_question}'. " \
             f"What plot can best represent this data?"
    response = gpt3.gpt_promt_davinci(prompt)
    query = response.replace("sample_data", "DATA")
    query = query.replace("\n", " ")
    # dataframe_new = duckdb.query(query).df()
    # print(dataframe_new)
    # st.session_state['question_dict'][new_question] = dataframe_new
    st.caption(f"Question: {new_question}")
    st.caption(f"Query: {query}")
    # st.bar_chart(dataframe_new)

@st.cache_data
def show_historical_data(old_question):
    st.caption(f"Question: {old_question}")
    dataframe_old = st.session_state['question_dict'][old_question]
    st.bar_chart(dataframe_old)

@st.cache_data
def get_data_overview(data):
    with st.spinner(text="In progress..."):
        prompt = f"Given the csv file with headers and sample data: {data} describe what each column means and what the dataset can be used for?"
        response = gpt3.gpt_promt_davinci(prompt)
        st.caption(response)

@st.cache_data
def get_raw_table(data):
    st.write(data)

def plot_scatter(dataframe):
    """

    :param dataframe:
    :return: Plot
    """


# Create a text element and let the reader know the data is loading.
DATA, sample_data_overview = load_data(UPLOADED_FILE)

if 'question_dict' not in st.session_state:
    st.session_state['question_dict'] = {}

#####################################################
st.markdown(f"### Overview of the data.")
get_data_overview(sample_data_overview)

# Inspecting raw data
st.subheader('Raw data')
get_raw_table(DATA)

st.subheader('Automated Visualizations')

new_question = st.text_input("Ask questions below and let AI do the visualization for you...", key = 'new_question')
add_new = st.button("Ask new question")

if add_new or new_question:
    if new_question not in st.session_state['question_dict']:
        print("New question: ", new_question)
        st.session_state['question_dict'][new_question] = ''
        for key in st.session_state['question_dict']:
            if new_question == key:
                add_new_row(sample_data_overview, key)
                pass
            else:
                # show_historical_data(key)
                pass

    else:
        st.warning(str(new_question)+" exists already!")




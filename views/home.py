import streamlit as st
import pandas as pd
import gpt3
import duckdb
import plotly

def load_view():
    st.markdown("# **Data Analytics AI**")
    st.markdown(
        "Uploading a csv, ask a question and gain insights from your data."
    )

    UPLOADED_FILE = st.file_uploader("Choose a file")
    GPT_SECRETS = st.secrets["gpt_secret"]
    gpt3.openai.api_key = GPT_SECRETS

    if not UPLOADED_FILE:
        UPLOADED_FILE = "sample_data.csv"
        st.warning("Using default dataset, upload a csv file to gain insights to your data...")

    # Store the initial value of widgets in session state
    if "visibility" not in st.session_state:
        st.session_state.visibility = "visible"
        st.session_state.disabled = False

    if 'question_dict_dataset input analysis - text' not in st.session_state:
        st.session_state['question_dict_dataset input analysis - text'] = {}
        st.session_state['question_dict_dataset input analysis - visuals'] = {}
        st.session_state['question_dict_general - non dataset related'] = {}

    if 'generated_dataset input analysis - text' not in st.session_state:
        st.session_state['generated_dataset input analysis - text'] = []
        st.session_state['generated_dataset input analysis - visuals'] = []
        st.session_state['generated_general - non dataset related'] = []

    if 'past_dataset input analysis - text' not in st.session_state:
        st.session_state['past_dataset input analysis - text'] = []
        st.session_state['past_dataset input analysis - visuals'] = []
        st.session_state['past_general - non dataset related'] = []

    if "disabled_input" not in st.session_state:
        st.session_state["disabled_input"] = False

    @st.cache_resource
    def load_data(UPLOADED_FILE):
        if UPLOADED_FILE is not None:
            data = pd.read_csv(UPLOADED_FILE)
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
    def get_summary_statistics(dataframe):
        with st.spinner(text="In progress..."):
            description = dataframe.describe()
            get_raw_table(description)
            json_description = description.to_json()
            prompt = f"Given the summary description of the data below: {json_description}, " \
                     f"explain the result given in full detail."
            response = gpt3.gpt_promt(prompt)
            st.caption(response['content'])

            description_objects = dataframe.describe(include=['O'])
            get_raw_table(description_objects)
            prompt_2 = f"Given the summary description of the data below of categorical data: {description_objects}, " \
                     f"explain the result given in full detail."
            response = gpt3.gpt_promt(prompt_2)
            st.caption(response['content'])


    @st.cache_data
    def query(sample_data_overview, new_question):
        prompt = f"Given the csv file sample data with headers: {sample_data_overview}, write a sql script with given dataset columns to get '{new_question}'. " \
                 f"What plot can best represent this data?"
        response = gpt3.gpt_promt_davinci(prompt)
        query = response.replace("sample_data", "DATA")
        query = query.replace("\n", " ")
        dataframe_new = duckdb.query(query).df()
        st.session_state['question_dict_dataset input analysis - visuals'][new_question] = dataframe_new
        return response

    @st.cache_data
    def query_text(sample_data_overview, new_question):
        prompt = f"Given the csv file sample data with headers: {sample_data_overview}, write a sql script with given dataset columns to get '{new_question}'. "
        response = gpt3.gpt_promt_davinci(prompt)
        query = response.replace("sample_data", "DATA")
        query = query.replace("\n", " ")
        dataframe_new = duckdb.query(query).df().head(50)
        if len(dataframe_new) >0:
            dataframe_json = dataframe_new.to_json()
            prompt = f"Please give a summary of the result in human readable text: " \
                     f"The question '{new_question}' was asked. The result has been generated using {query}," \
                     f"Answering in a way that answers the question, explain the result: {dataframe_json}"
            response = gpt3.gpt_promt_davinci(prompt)
        else:
            prompt = f"Please write an explaination using simple terms on why the question asked cannot be answered:" \
                     f"Using the dataset {sample_data_overview}, with '{query}' produced no result, " \
                     f"when the question '{new_question}' was asked."
            response = gpt3.gpt_promt_davinci(prompt)
        return response

    @st.cache_data
    def query_basic(new_question):
        prompt = f"As an acturary answer the following question:  '{new_question}'."
        response = gpt3.gpt_promt_davinci(prompt)
        return response

    @st.cache_data
    def show_historical_data(old_question):
        st.caption(f"Question: {old_question}")
        dataframe_old = st.session_state['question_dict'][old_question]
        st.bar_chart(dataframe_old)

    @st.cache_data
    def get_data_overview(data):
        with st.spinner(text="In progress..."):
            prompt = f"Given the csv file with headers and sample data: {data} describe what each " \
                     f"column means and what the dataset can be used for?"
            response = gpt3.gpt_promt_davinci(prompt)
            st.caption(response)

    @st.cache_data
    def get_raw_table(data):
        st.write(data)

    def ask_new_question(question_option):
        text = st.empty()

        index_questions = 'question_dict_' + question_option
        index_generated = 'generated_' + question_option
        index_past = 'past_' + question_option

        if question_option == 'dataset input analysis - text':
            new_question = text.text_input("Ask questions below and talk to our ai...", key = question_option)
        elif question_option == 'dataset input analysis - visuals':
            new_question = text.text_input("Ask questions below and talk to our ai...", key = question_option)
        else:
            new_question = text.text_input("Ask questions below and talk to our ai...", key = question_option)

        if new_question:
            if new_question not in st.session_state[index_questions]:
                st.session_state[index_questions][new_question] = ''
                for key in st.session_state[index_questions]:
                    if new_question == key:
                        if question_option == 'dataset input analysis - text':
                            output = query_text(sample_data_overview, key)
                        elif question_option == 'dataset input analysis - visuals':
                            output = query(sample_data_overview, key)
                        else:
                            output = query_basic(key)

                        st.session_state[index_past].append(new_question)
                        st.session_state[index_generated].append(output)

            else:
                st.warning('Question exists...', icon="⚠️")

        with st.spinner(text="In progress..."):
            if st.session_state[index_generated]:
                for i in range(len(st.session_state[index_generated])-1, -1, -1):
                    try:
                        st.text("Question: " + st.session_state[index_past][i])
                        # st.text_area(label = "😀Question", value = (st.session_state[index_past][i]).strip(), disabled=True)
                        st.text_area(label = "Answer🤖", value = (st.session_state[index_generated][i]).strip(), disabled=True)
                    except:
                        pass


    if UPLOADED_FILE is not None:
        # Create a text element and let the reader know the data is loading.
        DATA, sample_data_overview = load_data(UPLOADED_FILE)

        #####################################################
        st.markdown(f"### Overview of the data.")
        get_data_overview(sample_data_overview)

        # Inspecting raw data
        st.subheader('Raw data')
        get_raw_table(DATA)

        # Inspecting summary statistics
        st.subheader('Summary Statistics')
        get_summary_statistics(DATA)

        with st.sidebar:
            st.markdown("# AutoViZChat💬")
            question_option = st.selectbox(
                "What type of question-answer would you like?",
                ("Dataset Input Analysis - Text", "Dataset Input Analysis - Visuals", "General - Non dataset related"),
                label_visibility=st.session_state.visibility,
                disabled=st.session_state.disabled,
            )

            ask_new_question(question_option.lower())


    else:
        with st.sidebar:
            st.markdown("# AutoViZChat💬")
            st.text("Waiting for dataset to be uploaded...")





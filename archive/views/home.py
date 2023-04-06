import streamlit as st
import pandas as pd
import gpt3
import duckdb
import plotly
import re
import os

def load_view():
    st.markdown("# **Data Analytics AI**")
    st.markdown(
        "Uploading a csv, ask a question and gain insights from your data."
    )

    UPLOADED_FILE = st.file_uploader("Choose a file")
    GPT_SECRETS = st.secrets["gpt_secret"]
    gpt3.openai.api_key = GPT_SECRETS

    if not UPLOADED_FILE:
        UPLOADED_FILE = "./views/sample_data.csv"
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

    if "sql_results" not in st.session_state:
        st.session_state["sql_results"] = {}


    @st.cache_resource
    def load_data(UPLOADED_FILE):
        if UPLOADED_FILE is not None:
            data = pd.read_csv(UPLOADED_FILE)
            lowercase = lambda x: str(x).lower()
            data.rename(lowercase, axis='columns', inplace=True)
            data = rename_dataset_columns(data)

        data_random_sample = data.sample(frac=0.05)
        rows = data_random_sample.values.tolist()
        header = data_random_sample.columns.tolist()
        sample_data_overview = header + rows[:10]
        return data, sample_data_overview

    @st.cache_data
    def get_data_overview(header):
        with st.spinner(text="In progress..."):
            prompt =  f"Format your answer to markdown latex. Use markdown font size 3. " \
                      f"Please do not include heading or subheading."\
                      f"Given the csv file with headers: {header} " \
                      f"You are an actuary, " \
                      f"Describe what each column means and what the dataset can be used for?"

            response = gpt3.gpt_promt(prompt)
            st.markdown(response['content'])
        if 'question_dict' not in st.session_state:
            st.session_state['question_dict'] = {}

    @st.cache_data
    def rename_dataset_columns(dataframe):
        dataframe.columns = dataframe.columns.str.replace('[#,@,&,$,(,)]', '')
        dataframe.columns = dataframe.columns.str.replace(' ', '_')
        dataframe.columns = [x.lstrip('_') for x in dataframe.columns]
        dataframe.columns = [x.strip() for x in dataframe.columns]
        return dataframe

    @st.cache_data
    def get_summary_statistics(dataframe):
        with st.spinner(text="In progress..."):

            # check dataframe dtype
            dtype_list = check_data_have_object(dataframe)

            if any(x in dtype_list for x in ['int64', 'float64']):
                st.info('Numerical dtype detected in data...')
                description = dataframe.describe()
                get_raw_table(description)
                json_description = description.to_json()
                prompt = f"Format your answer to markdown latex. Use markdown font size 3." \
                         f"Please do not include heading or subheading." \
                         f"Given the summary description of the data below: {json_description}, " \
                         f"You are an actuary, " \
                         f"Explain the result given in full detail. "
                response = gpt3.gpt_promt(prompt)
                st.markdown(response['content'])

            if any(x in dtype_list for x in ['O']):
                st.info('Numerical dtype detected in data...')
                description_objects = dataframe.describe(include=['O'])
                get_raw_table(description_objects)
                prompt_2 =  f"Format your answer to markdown latex. Use markdown font size 3." \
                            f"Please do not include heading or subheading." \
                            f"Given the summary description of the data below of categorical data: {description_objects}, " \
                            f"You are an actuary, " \
                            f"explain the result given in full detail "
                response = gpt3.gpt_promt(prompt_2)
                st.markdown(response['content'])


    @st.cache_data
    def query(sample_data_overview, new_question):
        prompt = f"You are an actuary, " \
                 f"Given the csv file sample data with headers: {sample_data_overview}, " \
                 f"write a sql script with given dataset columns to get '{new_question}'. " \
                 f"What plot can best represent this data?"
        response = gpt3.gpt_promt_davinci(prompt)
        query = response.replace("sample_data", "DATA")
        query = query.replace("\n", " ")
        dataframe_new = duckdb.query(query).df()
        st.session_state['question_dict_dataset input analysis - visuals'][new_question] = dataframe_new
        return response

    @st.cache_data
    def generate_sql_gpt(sample_data_overview, new_question):
        print("Query: ", new_question)
        prompt = f"You are an actuary, " \
                 f"Given the csv file sample data with headers: {sample_data_overview}, " \
                 f"write a sql script for duckdb with given dataset columns to get '{new_question}'. "
        response = gpt3.gpt_promt_davinci(prompt)
        query = response.replace("sample_data", "DATA")
        query = query.replace("\n", " ")
        query = re.search(r"(SELECT .*)\;", query).group(1)

        return query

    @st.cache_data
    def query_no_result(sample_data_overview, new_question, sql_query):
        prompt = f"You are an actuary, " \
                 f"Given the csv file sample data with headers: {sample_data_overview}, " \
                 f"you have generated no result for the question '{new_question}'. " \
                 f"using the sql query '{sql_query}'. " \
                 f"explain why no result is given? is it missing column?" \
                 f"If column is missing, ask user to rename the column in csv" \
                 f"Do not show the query in the answer."
        response = gpt3.gpt_promt_davinci(prompt)
        return response

    @st.cache_data
    def get_dataframe_from_duckdb_query(query):
        try:
            dataframe_new = duckdb.query(query).df().head(50)
        except:
            dataframe_new = pd.DataFrame()
        return dataframe_new

    @st.cache_data
    def query_text(sample_data_overview, new_question):

        # Get the query
        query = generate_sql_gpt(sample_data_overview, new_question)

        print("Query: ", query)
        dataframe_new = get_dataframe_from_duckdb_query(query)

        if len(dataframe_new) >0:
            dataframe_json = dataframe_new.to_json()
            prompt = f"You are an actuary, " \
                     f"Please give a summary of the result in human readable text: " \
                     f"The question '{new_question}' was asked. The result has been generated using {query}," \
                     f"Answering in a way that answers the question, explain the result: {dataframe_json}" \
                     f"Do not show the query in the answer."
            response = gpt3.gpt_promt_davinci(prompt)
        else:
            response = query_no_result(sample_data_overview, new_question, query)
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
    def get_raw_table(data):
        st.write(data)

    @st.cache_data
    def check_data_have_object(data):
        resp = data.dtypes.to_list()
        return resp

    def ask_new_question(question_option):
        text = st.empty()

        index_questions = 'question_dict_' + question_option
        index_generated = 'generated_' + question_option
        index_past = 'past_' + question_option

        if question_option == 'dataset input analysis - text':
            new_question = text.text_input("Ask questions below and talk to our ai...", key = question_option).strip()
        elif question_option == 'dataset input analysis - visuals':
            new_question = text.text_input("Ask questions below and talk to our ai...", key = question_option).strip()
        else:
            new_question = text.text_input("Ask questions below and talk to our ai...", key = question_option).strip()

        if new_question:
            if new_question not in st.session_state[index_questions]:
                st.session_state[index_questions][new_question] = ''
                for key in st.session_state[index_questions]:
                    if new_question == key:
                        if question_option == 'dataset input analysis - text':
                            output = query_text(sample_data_overview, key)

                        elif question_option == 'dataset input analysis - visuals':
                            try:
                                output = query(sample_data_overview, key)
                            except:
                                output = "The query produce no result, please rephrase the question."
                        else:
                            try:
                                output = query_basic(key)
                            except:
                                output = "The query produce no result, please rephrase the question."

                        st.session_state[index_past].append(new_question)
                        st.session_state[index_generated].append(output)

            else:
                st.info('Question exists...', icon="⚠️")
                exist_question_index = st.session_state[index_past].index(new_question)
                exist_question = st.session_state[index_past].pop(exist_question_index)
                print(f"This question exists: {exist_question}")
                exist_output = st.session_state[index_generated].pop(exist_question_index)
                print(f"This output exists: {exist_output}")

                # Reinsert the question and output
                st.session_state[index_past].append(exist_question)
                st.session_state[index_generated].append(exist_output)

        with st.spinner(text="In progress..."):
            counter_non_result = 0
            if st.session_state[index_generated]:
                for i in range(len(st.session_state[index_generated])-1, -1, -1):
                    try:
                        if (st.session_state[index_generated][i]).strip() == "The query produce no result, please rephrase the question.":
                            counter_non_result += 1
                            if counter_non_result <= 1:
                                # if questions does not produce result,
                                # only show the first question and hide the rest
                                st.markdown("**Question: " + st.session_state[index_past][i] + "**")
                                st.text_area(label = "Answer🤖", value = ("The query produce no result, please rephrase the question.").strip(), disabled=True)
                        else:
                            # if questions have result print them out
                            st.markdown("**Question: " + st.session_state[index_past][i] + "**")
                            height_adjustor = len((st.session_state[index_generated][i]).strip())*0.75
                            st.text_area(label = "Answer🤖", value = (st.session_state[index_generated][i]).strip(), disabled=True,
                                         height=int(height_adjustor))
                    except:
                        pass


    if UPLOADED_FILE is not None:
        # Create a text element and let the reader know the data is loading.
        DATA, sample_data_overview = load_data(UPLOADED_FILE)

        #####################################################
        st.markdown(f"### Overview of the data")
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





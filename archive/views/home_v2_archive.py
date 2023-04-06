
import os

import streamlit as st
import pandas as pd
import gpt3
import duckdb
import plot
import re
import os

def load_view():
    st.markdown("# **Data Analytics AI**")
    st.markdown(
        "Uploading a csv, ask a question and gain insights from your data."
    )

    UPLOADED_FILE = st.file_uploader("Choose a file")
    GPT_SECRETS = st.secrets["gpt_secret"]
    SIDE_BAR_QUESTION_TAB_1 = 'question_dict_dataset input analysis'
    SIDE_BAR_QUESTION_TAB_2 = 'question_dict_general - non dataset related'
    SIDE_BAR_GENERATED_DATASET_INPUT_1 = 'generated_dataset input analysis'
    SIDE_BAR_GENERATED_DATASET_INPUT_2 = 'generated_general - non dataset related'
    SIDE_BAR_PAST_DATASET_INPUT_1 = 'past_dataset input analysis'
    SIDE_BAR_PAST_DATASET_INPUT_2 = 'past_general - non dataset related'
    gpt3.openai.api_key = GPT_SECRETS

    if not UPLOADED_FILE:
        UPLOADED_FILE = "./views/sample_data.csv"
        st.warning("Using default dataset, upload a csv file to gain insights to your data...")

    # Store the initial value of widgets in session state
    if "visibility" not in st.session_state:
        st.session_state.visibility = "visible"
        st.session_state.disabled = False

    if 'question_dict_dataset input analysis' not in st.session_state:
        st.session_state[SIDE_BAR_QUESTION_TAB_1] = {}
        st.session_state[SIDE_BAR_QUESTION_TAB_2] = {}

    if 'generated_dataset input analysis' not in st.session_state:
        st.session_state[SIDE_BAR_GENERATED_DATASET_INPUT_1] = []
        st.session_state[SIDE_BAR_GENERATED_DATASET_INPUT_2] = []

    if 'past_dataset input analysis' not in st.session_state:
        st.session_state[SIDE_BAR_PAST_DATASET_INPUT_1] = []
        st.session_state[SIDE_BAR_PAST_DATASET_INPUT_2] = []

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
                      f"Please do not include heading or subheading." \
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
    def convert_datatype(df):
        """Automatically detect and convert (in place!) each
        dataframe column of datatype 'object' to a datetime just
        when ALL of its non-NaN values can be successfully parsed
        by pd.to_datetime().  Also returns a ref. to df for
        convenient use in an expression.
        """
        from pandas.errors import ParserError
        for c in df.columns[df.dtypes=='object']: #don't cnvt num
            try:
                df[c]=pd.to_datetime(df[c])
            except (ParserError,ValueError): #Can't cnvrt some
                pass # ...so leave whole column as-is unconverted

        df = df.convert_dtypes()
        return df

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
    def generate_sql_gpt(_data_schema, new_question):
        print("Query: ", new_question)
        prompt = f"""
        
        Example Context: 
        You are an actuary
        Given the data with schema:
        dict_items([('age', Int64Dtype()), ('sex', string[python]), ('bmi', Float64Dtype()), ('children', Int64Dtype()), ('smoker', string[python]), ('region', string[python]), ('charges', Float64Dtype())])
        
        
        Example Question: 
        write me an SQL script that can answer the following question: "how many authors are there in the year 2022". 
        Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction.
        
        Recommend a chart plot using Streamlit (st) charting.  Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>". 
        IF SQL script has 1 column, recommend st.metric.
        IF SQL script has 2 columns, recommend st.barchart, or st.line_chart based on schema of SQL column.
        IF SQL script select statment has more than 3 columns, recommend st.table.
        
        
        Recommend the x and y variables for the plot. Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>" and y in the tag "<y_var_start>" and "<y_var_end>" .
        IF SQL script has 1 column, and chart type is st.metric. put y as None
        IF SQL script has more than 3 columns, and recommend chart type is st.table. put None for x and y.
        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>".
        
        Example Answer: 
        <sql_start>
        SELECT COUNT(DISTINCT author) as author_count, date
        FROM DATA
        WHERE YEAR(date) = 2022
        <sql_end>
        
        <chart_start>
        st.bar_chart
        <chart_end>
        
        <x_var_start>
        date
        <x_var_end>
        
        <y_var_start>
        author_count
        <y_var_end>
        
        <title_start>
        The count of authors over date
        <title_end>
        
        
        Example Context: 
        You are an actuary
        Given the data with schema:
        dict_items([('age', Int64Dtype()), ('sex', string[python]), ('bmi', Float64Dtype()), ('children', Int64Dtype()), ('smoker', string[python]), ('region', string[python]), ('charges', Float64Dtype())])
        
        
        Example Question: 
        Write me an SQL script that can answer the following question: "how many authors are there?". 
        Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. Please give column names after the transformation.
        
        Recommend a chart plot using Streamlit (st) charting.  Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>". 
        IF SQL script has 1 column, recommend st.metric.
        IF SQL script has 2 columns, recommend st.barchart, or st.line_chart based on schema of SQL column.
        IF SQL script select statment has more than 3 columns, recommend st.table.
        
        Recommend the x and y variables for the plot. Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>" and y in the tag "<y_var_start>" and "<y_var_end>" .
        IF SQL script has 1 column, and chart type is st.metric. put y as None
        IF SQL script has more than 3 columns, and recommend chart type is st.table. put None for x and y.
        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>".
        
        
        Example Answer: 
        <sql_start>
        SELECT COUNT(DISTINCT author) as author_count
        FROM DATA
        <sql_end>
        
        <chart_start>
        st.metric
        <chart_end>
        
        <x_var_start>
        author_count
        <x_var_end>
        
        <y_var_start>
        None
        <y_var_end>
        
        <title_start>
        The count of authors
        <title_end>

        
        Context: 
        You are an actuary
        Given the data with schema: {_data_schema}
        
        
        Question: 
        Write me an SQL script that can answer the following question: "{new_question}". 
        Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. Please give column names after the transformation.
        
        Recommend a chart plot using Streamlit (st) charting.  Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>". 
        IF SQL script has 1 column, recommend st.metric.
        IF SQL script has 2 columns, recommend st.barchart, or st.line_chart based on schema of SQL column.
        IF SQL script select statment has more than 3 columns, recommend st.table.
        
        Recommend the x and y variables for the plot. Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>" and y in the tag "<y_var_start>" and "<y_var_end>" .
        IF SQL script has 1 column, and chart type is st.metric. put y as None
        IF SQL script has more than 3 columns, and recommend chart type is st.table. put None for x and y.
        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>".
        
        """
        response = gpt3.gpt_promt_davinci(prompt)
        query_recommendation = re.search(r"<sql_start>(.*)<sql_end>", response.replace("\n", ' ')).group(1).strip()
        chart_recommendation = re.search(r"<chart_start>(.*)<chart_end>", response.replace("\n", ' ')).group(1).strip()
        x_recommendation = re.search(r"<x_var_start>(.*)<x_var_end>", response.replace("\n", ' ')).group(1).strip()
        y_recommendation = re.search(r"<y_var_start>(.*)<y_var_end>", response.replace("\n", ' ')).group(1).strip()
        title_recommendation = re.search(r"<title_start>(.*)<title_end>", response.replace("\n", ' ')).group(1).strip()

        return query_recommendation, chart_recommendation, x_recommendation, y_recommendation, title_recommendation

    @st.cache_data
    def query_no_result(_sample_data_overview, new_question, sql_query):

        prompt = f"You are an actuary, " \
                 f"Given the csv file sample data with headers: {_sample_data_overview}, " \
                 f"you have generated no result for the question '{new_question}'. " \
                 f"using the sql query '{sql_query}'. " \
                 f"explain why no result is given? is it missing column?" \
                 f"If column is missing, ask user to rename the column in csv" \
                 f"Do not show the query in the answer."
        response = gpt3.gpt_promt_davinci(prompt)
        return response

    @st.cache_data
    def explain_result(query_recommendation, new_question, dataframe_json):
        prompt = f"You are an actuary, " \
                 f"Please give a summary of the result in human readable text: " \
                 f"The question '{new_question}' was asked. The result has been generated using {query_recommendation}," \
                 f"Answering in a way that answers the question, explain the result: {dataframe_json}" \
                 f"Do not show the query in the answer."
        response = gpt3.gpt_promt_davinci(prompt)
        return response
    @st.cache_data
    def get_dataframe_from_duckdb_query(query):
        try:
            # dataframe_new = duckdb.query(query).df().head(50)
            dataframe_new = duckdb.query(query).df()
        except:
            dataframe_new = pd.DataFrame()
        return dataframe_new

    @st.cache_data
    def query_text(_schema_data, new_question):

        # Get the query
        query_recommendation, chart_recommendation, x_recommendation, y_recommendation, title_recommendation = generate_sql_gpt(schema_data, new_question)

        print("Query: ", query_recommendation)
        dataframe_new = get_dataframe_from_duckdb_query(query_recommendation)

        if len(dataframe_new) > 0:
            dataframe_json = dataframe_new.to_json()
            response = explain_result(query_recommendation, new_question, dataframe_json)
        else:
            response = query_no_result(_schema_data, new_question, query_recommendation)
            chart_recommendation = None
            x_recommendation = None
            y_recommendation = None
        return response, chart_recommendation, x_recommendation, y_recommendation, title_recommendation, dataframe_new

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

    def ask_new_question(question_option, schema_data):
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
                        if question_option == 'dataset input analysis':
                            output, chart_recommendation, x_recommendation, y_recommendation, title_recommendation, dataframe_output = query_text(schema_data, key)

                            print("chart_recommendation: ", chart_recommendation)
                            print("x_recommendation: ", x_recommendation)
                            print("y_recommendation: ", y_recommendation)
                            print(dataframe_output)

                            if chart_recommendation == "st.metric":
                                plot.plot_metrics(dataframe_output, title_recommendation, x_recommendation)

                            if chart_recommendation == "st.line_chart":
                                x_recommendation = x_recommendation.split(",")[0]
                                st.line_chart(data=dataframe_output, x=x_recommendation, y=y_recommendation, use_container_width=True)

                            if chart_recommendation == "st.bar_chart":
                                x_recommendation = x_recommendation.split(",")[0]
                                st.bar_chart(data=dataframe_output, x=x_recommendation, y=y_recommendation, use_container_width=True)

                            if chart_recommendation == "st.table":
                                st.table(data=dataframe_output.head())

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

        DATA = convert_datatype(DATA)
        schema_data = DATA.dtypes.to_dict().items()

        with st.sidebar:
            st.markdown("# AutoViZChat💬")
            question_option = st.selectbox(
                "What type of question-answer would you like?",
                ("Dataset Input Analysis", "General - Non dataset related"),
                label_visibility=st.session_state.visibility,
                disabled=st.session_state.disabled,
            )

            ask_new_question(question_option.lower(), schema_data)


    else:
        with st.sidebar:
            st.markdown("# AutoViZChat💬")
            st.text("Waiting for dataset to be uploaded...")
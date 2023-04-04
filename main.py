# import streamlit_authenticator as stauth
import streamlit as st
# import yaml
# from yaml.loader import SafeLoader
from streamlit_elements import elements, mui, html
from streamlit_elements import dashboard
from pandas.errors import ParserError
import pandas as pd
import json
import gpt3
import duckdb
import plot
import re
import os
#
# # Login before displaying of webapp
# with open('config.yaml') as file:
#     config = yaml.load(file, Loader=SafeLoader)
#     print(config)
#
# authenticator = stauth.Authenticate(
#     config['credentials'],
#     config['cookie']['name'],
#     config['cookie']['key'],
#     config['cookie']['expiry_days'],
#     config['preauthorized']
# )
#
# name, authentication_status, username = authenticator.login('Login', 'main')
#
# if authentication_status:
st.markdown("# **Data Analytics AI**")
st.markdown(
    "Uploading a csv, ask a question and gain insights from your data."
)

UPLOADED_FILE = st.file_uploader("Choose a file")
GPT_SECRETS = st.secrets["gpt_secret"]
SIDE_BAR_QUESTION_TAB_1 = 'question_dict_normal'
SIDE_BAR_GENERATED_DATASET_INPUT_1 = 'generated_normal'
SIDE_BAR_PAST_DATASET_INPUT_1 = 'past_normal'
gpt3.openai.api_key = GPT_SECRETS

if not UPLOADED_FILE:
    UPLOADED_FILE = "./views/sample_data.csv"
    st.warning("Using default dataset, upload a csv file to gain insights to your data...")

# Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

if 'question_dict_normal' not in st.session_state:
    st.session_state[SIDE_BAR_QUESTION_TAB_1] = {}

if 'generated_normal' not in st.session_state:
    st.session_state[SIDE_BAR_GENERATED_DATASET_INPUT_1] = []

if 'past_normal' not in st.session_state:
    st.session_state[SIDE_BAR_PAST_DATASET_INPUT_1] = []

if "disabled_input" not in st.session_state:
    st.session_state["disabled_input"] = False

if "all_result" not in st.session_state:
    st.session_state["all_result"] = []


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
    # print("Query: ", new_question)
    prompt = f"""
    
    Example Context: 
    You are an actuary
    Given the data with schema:
    dict_items([('age', Int64Dtype()), ('sex', string[python]), ('bmi', Float64Dtype()), ('children', Int64Dtype()), ('smoker', string[python]), ('region', string[python]), ('charges', Float64Dtype())])
    
    
    Example Question: 
    write me an SQL script that can answer the following question: "how many authors are there in the year 2022". 
    Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction.
    
    Recommend a chart plot using Streamlit (st) charting.  Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>". 
    IF SQL script has 1 column, recommend st.metric unless max and min range of values is asked.
    IF range of values is asked, recommend st.metrics.
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
    IF SQL script has 1 column, recommend st.metric unless max and min range of values is asked.
    IF range of values is asked, recommend st.metrics.
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
    IF SQL script has 1 column, recommend st.metric unless max and min range of values is asked.
    IF range of values is asked, recommend st.metrics.
    IF SQL script has 2 columns, recommend st.barchart, or st.line_chart based on schema of SQL column.
    IF SQL script select statment has more than 3 columns, recommend st.table.
    
    Recommend the x and y variables for the plot. 
    Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>" and y in the tag "<y_var_start>" and "<y_var_end>".
    IF SQL script has 1 column, and chart type is st.metric. put y as None
    IF SQL script has more than 3 columns, and recommend chart type is st.table. put None for x and y.
    Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>".
    
    """
    response = gpt3.gpt_promt_davinci(prompt)
    try:
        query_recommendation = re.search(r"<sql_start>(.*)<sql_end>", response.replace("\n", ' ')).group(1).strip()
        chart_recommendation = re.search(r"<chart_start>(.*)<chart_end>", response.replace("\n", ' ')).group(1).strip()
        x_recommendation = re.search(r"<x_var_start>(.*)<x_var_end>", response.replace("\n", ' ')).group(1).strip()
        y_recommendation = re.search(r"<y_var_start>(.*)<y_var_end>", response.replace("\n", ' ')).group(1).strip()
        title_recommendation = re.search(r"<title_start>(.*)<title_end>", response.replace("\n", ' ')).group(1).strip()
    except:
        query_recommendation = None
        chart_recommendation = None
        x_recommendation = None
        y_recommendation = None
        title_recommendation = None

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
def explain_result(query_recommendation, new_question, dataframe_new):

    if len(dataframe_new ) > 50:
        correlation_matric = dataframe_new.corr().to_json()
        summary_statistics = dataframe_new.describe().to_json()
        trimmed_df = dataframe_new.sample(n=50).to_json()
        prompt = f"You are an actuary, " \
                 f"Please give a summary of the result in human readable text: " \
                 f"You are given the correlation metrics {correlation_matric} and the summary statistics {summary_statistics} generated from full dataset" \
                 f"The randomly sampled data is {trimmed_df}." \
                 f"Do not show the query in the answer." \
                 f"Answer the question '{new_question}'"
    else:
        dataframe_json = dataframe_new.to_json()
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
    # dataframe_new = duckdb.query(query).df()

    return dataframe_new

@st.cache_data
def query_text(_schema_data, new_question):

    # Get the query
    query_recommendation, chart_recommendation, x_recommendation, y_recommendation, title_recommendation = generate_sql_gpt(schema_data, new_question)

    # print("Query: ", query_recommendation)
    dataframe_new = get_dataframe_from_duckdb_query(query_recommendation)

    if len(dataframe_new) > 0:
        response = explain_result(query_recommendation, new_question, dataframe_new)
    else:
        response = query_no_result(_schema_data, new_question, query_recommendation)
        chart_recommendation = None
        x_recommendation = None
        y_recommendation = None
    return response, chart_recommendation, x_recommendation, y_recommendation, title_recommendation, query_recommendation

@st.cache_data
def create_sample_question(_schema_data):

    prompt = f"You are an data analyst, " \
             f"Create 5 questions based on {_schema_data} with less than 10 words per question. Make sure the questions are easy for you to answer" \
             f"Put each question in <question_start_1> question <question_end_1>, <question_start_2>, <question_start_3> respectively"
    response = gpt3.gpt_promt_davinci(prompt)

    try:
        question_1 = re.search(r"<question_start_1>(.*)<question_end_1>", response.replace("\n", ' ')).group(1).strip()
        question_2 = re.search(r"<question_start_2>(.*)<question_end_2>", response.replace("\n", ' ')).group(1).strip()
        question_3 = re.search(r"<question_start_3>(.*)<question_end_3>", response.replace("\n", ' ')).group(1).strip()
        question_4 = re.search(r"<question_start_4>(.*)<question_end_4>", response.replace("\n", ' ')).group(1).strip()
        question_5 = re.search(r"<question_start_5>(.*)<question_end_5>", response.replace("\n", ' ')).group(1).strip()
    except:
        question_1 = None
        question_2 = None
        question_3 = None
        question_4 = None
        question_5 = None
    return question_1, question_2, question_3, question_4, question_5

@st.cache_data
def get_raw_table(data):
    st.write(data)

@st.cache_data
def check_data_have_object(data):
    resp = data.dtypes.to_list()
    return resp

def check_layout_user_exists(username, path="session_layout/layout.json"):
    is_file_exists = os.path.exists(path)
    if is_file_exists:
        with open(path) as f:
            lines = f.readlines()
            layout_file = json.loads(str(lines))
    else:
        data = {username: []}
        with open("session_layout/layout.json", "w") as outfile:
            outfile.write(json.dumps(data, indent=4))

    # print("check", layout_file)
    if len(layout_file) > 0:
        user_layout = layout_file[username]
    else:
        user_layout = []

    return user_layout


def ask_new_question(sample_question, schema_data):
    text = st.empty()
    key_type = 'normal'
    index_questions = 'question_dict_' + key_type
    index_generated = 'generated_' + key_type
    index_past = 'past_' + key_type

    if sample_question:
        new_question = text.text_input("Try typing in your own question below...", value= sample_question, key = key_type).strip()
    else:
        new_question = text.text_input("Ask questions below and talk to our ai...", key = key_type).strip()

    if new_question:
        if new_question not in st.session_state[index_questions]:
            st.session_state[index_questions][new_question] = ''
            for key in st.session_state[index_questions]:
                if new_question == key:

                    output, chart_recommendation, x_recommendation, y_recommendation, title_recommendation, query_recommendation = query_text(schema_data, key)

                    resp = {
                        "question": new_question,
                        "query_recommendation": query_recommendation,
                        "chart_recommendation": chart_recommendation,
                        "x_recommendation": x_recommendation,
                        "y_recommendation": y_recommendation,
                        "title_recommendation": title_recommendation
                    }

                    print(resp)

                    st.session_state[index_past].append(new_question)
                    st.session_state[index_generated].append(output)
                    st.session_state["all_result"].append(resp)

        else:
            st.info('Question exists...', icon="⚠️")
            exist_question_index = st.session_state[index_past].index(new_question)
            exist_question = st.session_state[index_past].pop(exist_question_index)
            # print(f"This question exists: {exist_question}")
            exist_output = st.session_state[index_generated].pop(exist_question_index)
            # print(f"This output exists: {exist_output}")

            # Reinsert the question and output
            st.session_state[index_past].append(exist_question)
            st.session_state[index_generated].append(exist_output)

    # Plot element dashboard
    with elements("dashboard"):

        # initialize layout
        # check_layout_user_exists(username)
        counter_recommendation = 0
        layout = []

        # You can create a draggable and resizable dashboard using
        for recommendation in st.session_state["all_result"]:
            question = recommendation['question']
            chart_recommendation = recommendation['chart_recommendation']
            if "bar" in chart_recommendation.lower():

                # First, build a default layout for every element you want to include in your dashboard
                item_key = "item_" + str(question)

                if len(layout) > 0:
                    for layer in layout:
                        # print("layer number", layer)
                        if layer['i'] == item_key:
                            layout = layout + [
                                # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
                                dashboard.Item(item_key, layer['x'], layer['y'], layer['w'], layer['h'], isResizable=True, isDraggable=True)
                            ]
                        else:
                            layout = layout + [
                                # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
                                dashboard.Item(item_key, 0, counter_recommendation, 2, 2, isResizable=True, isDraggable=True)
                            ]
                else:
                    layout = layout + [
                        # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
                        dashboard.Item(item_key, 0, counter_recommendation, 2, 2, isResizable=True, isDraggable=True)
                    ]
                counter_recommendation += 1

        def handle_layout_change(updated_layout):
            # You can save the layout in a file, or do anything you want with it.
            # You can pass it back to dashboard.Grid() if you want to restore a saved layout.
            print("Updated Layout", updated_layout)
            # data = {username: updated_layout}
            # with open("session_layout/sample.json", "w") as outfile:
            #     outfile.write(json.dumps(data, indent=4))

        with dashboard.Grid(layout, onLayoutChange=handle_layout_change):
            for recommendation in st.session_state["all_result"]:
                query_recommendation = recommendation['query_recommendation']
                question = recommendation['question']
                x_recommendation = recommendation['x_recommendation']
                y_recommendation = recommendation['y_recommendation']
                chart_recommendation = recommendation['chart_recommendation']
                title_recommendation = recommendation['title_recommendation']
                item_key = "item_" + str(question)

                # Get new dataframe
                dataframe_new = get_dataframe_from_duckdb_query(query_recommendation)
                # print(dataframe_new)

                if "bar" in chart_recommendation.lower():
                    with mui.Paper(label=question ,elevation=3, variant="outlined", square=True, key=item_key):
                        plot.create_bar_chart(dataframe_new, x_recommendation, y_recommendation)
                elif "metric" in chart_recommendation.lower():
                    with mui.Paper(label=question ,elevation=10, variant="outlined", square=True, key=item_key):
                        plot.create_metric_chart(dataframe_new, x_recommendation, title_recommendation)


    counter_non_result = 0
    counter_message_limit = 0
    if st.session_state[index_generated]:
        placeholder = st.empty()
        with placeholder.container():
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
                        # Show the lastest 5 message
                        # if questions have result print them out
                        st.markdown("**Question: " + st.session_state[index_past][i] + "**")
                        height_adjustor = len((st.session_state[index_generated][i]).strip())*0.45
                        st.text_area(label = "Answer🤖", value = (st.session_state[index_generated][i]).strip(), disabled=True,
                                     height=int(height_adjustor))
                        counter_message_limit += 1
                        # print(counter_message_limit)
                except:
                    pass


if UPLOADED_FILE is not None:
    # Create a text element and let the reader know the data is loading.
    DATA, sample_data_overview = load_data(UPLOADED_FILE)

    #####################################################
    with st.expander("See data explaination"):
        get_data_overview(sample_data_overview)

    # Inspecting raw data
    with st.expander("See raw data"):
        get_raw_table(DATA)

    # Inspecting summary statistics
    with st.expander("See summary statistics"):
        get_summary_statistics(DATA)

    data_schema = convert_datatype(DATA)
    schema_data = data_schema.dtypes.to_dict().items()

    st.markdown("### AIViz💬")
    st.write("List of sample questions")
    col1, col2, col3, col4, col5 = st.columns(5)

    # Generate 5 sample questions
    sample_question_1, sample_question_2, sample_question_3, sample_question_4, sample_question_5 = create_sample_question(schema_data)
    question = None

    # Create the sample questions columns
    with col1:
        if st.button(sample_question_1):
            question = sample_question_1

    with col2:
        if st.button(sample_question_2):
            question = sample_question_2

    with col3:
        if st.button(sample_question_3):
            question = sample_question_3

    with col4:
        if st.button(sample_question_4):
            question = sample_question_4

    with col5:
        if st.button(sample_question_5):
            question = sample_question_5

    # Generate the ask question bar
    ask_new_question(question, schema_data)
    # elif authentication_status is False:
    #     st.error('Username/password is incorrect')
    # elif authentication_status is None:
    #     st.warning('Please enter your username and password')








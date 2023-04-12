# import streamlit_authenticator as stauth
import streamlit as st
# import yaml
# from yaml.loader import SafeLoader
from streamlit_elements import elements, mui, html
from streamlit_elements import dashboard
from pandas.errors import ParserError
import altair as alt
import pandas as pd
import numpy as np
import json
import gpt3
import duckdb
import plot
import re
import os
import random

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
    "Upload a csv, ask a question and gain insights from your data."
)

UPLOADED_FILE = st.file_uploader("Choose a file")
GPT_SECRETS = st.secrets["gpt_secret"]
SIDE_BAR_QUESTION_TAB_1 = 'question_dict_normal'
SIDE_BAR_GENERATED_DATASET_INPUT_1 = 'generated_normal'
SIDE_BAR_PAST_DATASET_INPUT_1 = 'past_normal'
gpt3.openai.api_key = GPT_SECRETS

if not UPLOADED_FILE:
    UPLOADED_FILE = "archive/views/sample_data.csv"
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

if 'question_dict' not in st.session_state:
    st.session_state['question_dict'] = {}


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
def get_raw_table(data):
    st.write(data)

@st.cache_data
def check_data_have_object(data):
    resp = data.dtypes.to_list()
    return resp

@st.cache_data
def get_data_overview(header):
    prompt =  f"Format your answer to markdown latex. Use markdown font size 3. " \
              f"Please do not include heading or subheading." \
              f"Given the csv file with headers: {header} " \
              f"You are an actuary, " \
              f"Describe what each column means and what the dataset can be used for?"

    response = gpt3.gpt_promt(prompt)
    st.markdown(response['content'])

@st.cache_data
def get_summary_statistics(dataframe):

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
    You are a data analyst
    Given the data with schema:
    dict_items([('key', string[python]), ('author', string[python]), ('date', dtype('<M8[ns]')), ('stars', Int64Dtype()), ('title', string[python]), ('helpful_yes', Int64Dtype()), ('helpful_no', Int64Dtype()), ('text', string[python])])
    
    Example Question: 
    Write me an  SQL script in duckDB language that can answer the following question: "How many authors are there in the year 2022?". 
    Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. 
    Please give column names after the transformation and select an appropriate number of columns so that we can create a visualization from it.
    
    Answer: 
    <sql_start>
    SELECT COUNT(DISTINCT author) as author_count, date
    FROM DATA
    WHERE YEAR(date) = 2022
    <sql_end>
    
    Example Context: 
    You are a data analyst
    Given the data with schema:
    dict_items([('age', Int64Dtype()), ('sex', string[python]), ('bmi', Float64Dtype()), ('children', Int64Dtype()), ('smoker', string[python]), ('region', string[python]), ('charges', Float64Dtype())])
   
    Example Question: 
    Write me an  SQL script in duckDB language that can answer the following question: " What is the correlation between BMI and charges??". 
    Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. 
    Please give column names after the transformation and select an appropriate number of columns so that we can create a visualization from it.
    
    Answer: 
    <sql_start>
    SELECT CORR(charges, bmi) as correlation 
    FROM DATA
    <sql_end>
    
    Context: 
    You are a data analyst
    Given the data with schema: 
    {_data_schema}
    
    Question: 
    Write me an SQL script in duckDB language that can answer the following question:  {new_question}
    Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. 
    Please give column names after the transformation and select an appropriate number of columns so that we can create a visualization from it.
    
    """
    response = gpt3.gpt_promt_davinci(prompt)
    try:
        query_recommendation = re.search(r"<sql_start>(.*)<sql_end>", response.replace("\n", ' ')).group(1).strip()
    except:
        query_recommendation = None

    return query_recommendation

@st.cache_data
def query_chart_recommendation(_data_schema, new_question, recommened_query, number_of_records):
    prompt = f""" The schema of the data:
        dict_items([('age', Int64Dtype()), ('sex', string[python]), ('bmi', Float64Dtype()), ('children', Int64Dtype()), ('smoker', string[python]), ('region', string[python]), ('charges', Float64Dtype())])
        
        The data with the schema was transformed using:

        SELECT charges, region
        FROM DATA
        WHERE region = 'Southwest'
        AND charges < 100 OR charges > 10000
        
        Total number of records: 650

        Based on the question: "Given that I expect the medical charge to be around 100 to 10000 in the southwest region, what is the outlier of the charges in the southwest region?" and the query above, 
        recommend me a graph that can be used to best represent the question and the SQL generated.
        If total records is 1 and sql query has 1 column, recommend metric plot and recommended x variable.
        Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>".
        
        Recommend the x and y variables for the plot.
        Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>" .
        y in the tag "<y_var_start>" and "<y_var_end>" .
        hue/class in "<hue_var_start>" and "<hue_var_end>".
        Put numerical value for x and y. categorical value in hue.

        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>".
        
        <chart_start>box plot<chart_end>
        <x_var_start>region<x_var_end>
        <y_var_start>charges<y_var_end>
        <hue_var_start>None<hue_var_end>
        <title_start>Outliers of Medical Charges in the Southwest Region<title_end>

        The schema of the data:
        dict_items([('age', Int64Dtype()), ('sex', string[python]), ('bmi', Float64Dtype()), ('children', Int64Dtype()), ('smoker', string[python]), ('region', string[python]), ('charges', Float64Dtype())])
        
        The data with the schema was transformed using:
    
        SELECT age, sex, COUNT(*) as count
        FROM DATA
        WHERE region = 'southeast'
        GROUP BY age, sex
        
        Total number of records: 124

        Based on the question: "What is the distribution of age and sex of people in southeast region??" and the query above, 
        recommend me a graph that can be used to best represent the question and the SQL generated.
        If total records is 1 and sql query has 1 column, recommend metric plot and recommended x variable.
        Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>".
        
        Recommend the x and y variables for the plot.
        Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>".
        y in the tag "<y_var_start>" and "<y_var_end>" .
        hue/class in "<hue_var_start>" and "<hue_var_end>" .
        Put numerical value for x and y. categorical value in hue.

        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>"
        
        <chart_start>bar plot<chart_end>
        <x_var_start>age<x_var_end>
        <y_var_start>count<y_var_end>
        <hue_var_start>sex<hue_var_end>
        <title_start>Distribution of Age and Sex of People in Southeast Region<title_end>
        
        The schema of the data:
        dict_items([('age', Int64Dtype()), ('sex', string[python]), ('bmi', Float64Dtype()), ('children', Int64Dtype()), ('smoker', string[python]), ('region', string[python]), ('charges', Float64Dtype())])
        
        The data with the schema was transformed using:

        SELECT AVG(age) as avg_age
        FROM DATA
        
        Total number of records: 1

        Based on the question: "What is the average age of the people in the dataset?" and the query above, 
        recommend me a graph that can be used to best represent the question and the SQL generated.
        If total records is 1 and sql query has 1 column, recommend metric plot and recommended x variable.
        Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>".
        
        Recommend the x and y variables for the plot.
        Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>" .
        y in the tag "<y_var_start>" and "<y_var_end>" .
        hue/class in "<hue_var_start>" and "<hue_var_end>".
        Put numerical value for x and y. categorical value in hue.

        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>".
        
        <chart_start>metric<chart_end>
        <x_var_start>avg_age<x_var_end>
        <y_var_start>None<y_var_end>
        <hue_var_start>None<hue_var_end>
        <title_start>Average Age of People in the Dataset<title_end>
        
        The schema of the data:
        {_data_schema}
        
        The data with the schema was transformed using:
    
        {recommened_query}
        
        Total number of records: {number_of_records}

        Based on the question: {new_question} and the query above, 
        recommend me a graph that can be used to best represent the question and the SQL generated.
        If total records is 1 and sql query has 1 column, recommend metric plot and recommended x variable.
        Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>".
        
        Recommend the x and y variables for the plot.
        Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>".
        y in the tag "<y_var_start>" and "<y_var_end>" .
        hue/class in "<hue_var_start>" and "<hue_var_end>".
        Put numerical value for x and y. categorical value in hue.

        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>"

        """

    print(prompt)

    response = gpt3.gpt_promt_davinci(prompt)

    try:
        chart_recommendation = re.search(r"<chart_start>(.*)<chart_end>", response.replace("\n", ' ')).group(1).strip()
        x_recommendation = re.search(r"<x_var_start>(.*)<x_var_end>", response.replace("\n", ' ')).group(1).strip()
        y_recommendation = re.search(r"<y_var_start>(.*)<y_var_end>", response.replace("\n", ' ')).group(1).strip()
        hue_recommendation = re.search(r"<hue_var_start>(.*)<hue_var_end>", response.replace("\n", ' ')).group(1).strip()
        title_recommendation = re.search(r"<title_start>(.*)<title_end>", response.replace("\n", ' ')).group(1).strip()
    except:
        chart_recommendation = None
        x_recommendation = None
        y_recommendation = None
        hue_recommendation = None
        title_recommendation = None

    return chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation

@st.cache_data
def query_no_result(_sample_data_overview, new_question, sql_query):

    prompt = f"You are an actuary, " \
             f"Given the data with schema: {_sample_data_overview}, " \
             f"you have generated no result for the question '{new_question}'. " \
             f"using the sql query '{sql_query}'. " \
             f"explain why no result was returned." \
             f"Do not show the query in the answer."
    response = gpt3.gpt_promt_davinci(prompt)
    return response

@st.cache_data
def recursion_batch(list_of_df, list_of_result, new_question, query_recommendation):
    '''
    :param query_recommendation: The query that was created by GPT3 API
    :param new_question: The question that was asked by the user
    :param dataframe_new: The dataframe that was created in DuckDB with the query generated by GPT3
    :param list_of_result: Empty list to store the result from chat gpt
    :return: Recursive response from chat GPT
    '''

    print("Recursive batch length: ", len(list_of_df[0].to_json()))
    print("Recursive batch: ", list_of_df[0])
    print("Length: ", len(list_of_result))
    print("Content: ", list_of_result)
    if len(list_of_df) <= 10:
        if len(list_of_df) < 2:
            dataframe_json = list_of_df[0].to_json()
            prompt = f"You are an actuary, " \
                     f"Please give a report and insights of the result in human readable text: " \
                     f"The question '{new_question}' was asked. The result has been generated using {query_recommendation}," \
                     f"Answering in a way that answers the question, explain the result: {dataframe_json}" \
                     f"Do not show the query in the answer."
            list_of_result = list_of_result + [gpt3.gpt_promt_davinci(prompt)]
            return list_of_result
        else:
            dataframe_json = list_of_df[0].to_json()
            prompt = f"You are an actuary, " \
                     f"Please give a report and insights of the result in human readable text: " \
                     f"The question '{new_question}' was asked. The result has been generated using {query_recommendation}," \
                     f"Answering in a way that answers the question, explain the result: {dataframe_json}" \
                     f"Do not show the query in the answer."
            list_of_result = list_of_result + [gpt3.gpt_promt_davinci(prompt)]
            new_list = list_of_df[1:]
            return recursion_batch(new_list, list_of_result, new_question, query_recommendation)
    else:
        st.error('Performing huge data set analysis is disabled for now...')
        return "Sorry, we've disabled huge processing of large file insights for now..."

@st.cache_data
def recursive_summarizer_sub(list_of_response, list_of_result_response, new_question):

    if len(list_of_response) < 2:
        list_of_result_response = list_of_result_response + list_of_response
        return list_of_result_response
    else:
        data = '\n'.join(list_of_response[0])
        prompt = f"Given the question is {new_question}." \
                 f"Summarize the following text after: {data}"
        list_of_result_response = list_of_result_response + [gpt3.gpt_promt_davinci(prompt)]
        new_list = list_of_response[1:]
        return recursive_summarizer_sub(new_list, list_of_result_response, new_question)

# def recursive_summarizer_main(response, list_of_response, new_question):
#     if len(response) < 2:
#         return response[0]
#     else:
#         list_of_summarize_text = []
#         response = recursive_summarizer_sub(response, list_of_summarize_text, new_question)
#         return recursive_summarizer_main(response, list_of_response, new_question)

@st.cache_data
def split_words_into_sublists(word_list, max_words_per_list):
    """
    Joins words in a list together and splits them into sublists with a maximum word count
    of `max_words_per_list`.

    Args:
        word_list (list): List of words.
        max_words_per_list (int): Maximum word count per sublist.

    Returns:
        list: List of sublists containing words.
    """
    # Join words into a single string
    joined_words = ' '.join(word_list)

    # Split words into sublists of max_words_per_list each
    sublists = [joined_words[i:i + max_words_per_list] for i in range(0, len(joined_words), max_words_per_list)]

    return sublists

@st.cache_data
def explain_result(query_recommendation, new_question, dataframe_new):

    batch_size = round(len(dataframe_new.to_json())/ 3200 ) + (len(dataframe_new.to_json()) % 3200 > 0)
    print(f"Batch size: {batch_size}")
    list_of_df = np.array_split(dataframe_new, batch_size)
    # sample data to first 10 dataframe to get result, to remove in prod
    list_of_df = list_of_df[:3]
    list_of_result = []

    with st.spinner("Working on the analysis, please wait..."):
        response = recursion_batch(list_of_df, list_of_result, new_question, query_recommendation)

    if response:
        list_of_result_response = []
        st.success('Done!')
        if len(response) >= 2:
            print("Processing sub explaination")
            max_words_per_list = 3500
            sublists = split_words_into_sublists(response, max_words_per_list)
            response = recursive_summarizer_sub(sublists, list_of_result_response, new_question)
            response = '\n'.join(response)
        else:
            print("Combining the response")
            response = '\n'.join(response)

    return response

@st.cache_data
def get_dataframe_from_duckdb_query(query):
    try:
        dataframe_new = duckdb.query(query).df()
    except:
        dataframe_new = pd.DataFrame()
    print(dataframe_new)
    return dataframe_new

@st.cache_data
def query_text(_schema_data, new_question):
    print("Querying the GPT...")
    # Get the query
    query_recommendation = re.sub(" +", " ", generate_sql_gpt(schema_data, new_question))
    dataframe_new = get_dataframe_from_duckdb_query(query_recommendation)
    chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation = query_chart_recommendation(schema_data, new_question, query_recommendation, len(dataframe_new))

    if len(dataframe_new) > 0:
        response = explain_result(query_recommendation, new_question, dataframe_new)
        print("Response", response)
    else:
        response = query_no_result(_schema_data, new_question, query_recommendation)
        chart_recommendation = None
        x_recommendation = None
        y_recommendation = None
        hue_recommendation = None
        title_recommendation = None

    return response, chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation, query_recommendation

@st.cache_data
def create_sample_question(schema_data, data):

    summary_statistics = data.describe()
    corr_data = data.corr()

    prompt = f"You are an data analyst, " \
             f"Generate me 50 questions based on data using the schema {schema_data}, use " \
             f"summary statistics: {summary_statistics} and" \
             f"correlation statistics: {corr_data}. to generate more questions" \
             f"Put each question in <question_start> your generated question <question_end>."

    response = gpt3.gpt_promt_davinci(prompt)

    try:
        questions = re.findall("<question_start>(.*?)<question_end>", response.replace("\n", ' '))
        n = 5
        random_choice = random.sample(questions, k=n)
        question_1 = random_choice[0]
        question_2 = random_choice[1]
        question_3 = random_choice[2]
        question_4 = random_choice[3]
        question_5 = random_choice[4]
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

                    output, chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation, query_recommendation = query_text(schema_data, key)

                    if chart_recommendation != None:
                        resp = {
                            "question": new_question,
                            "query_recommendation": query_recommendation,
                            "chart_recommendation": chart_recommendation,
                            "x_recommendation": x_recommendation,
                            "y_recommendation": y_recommendation,
                            "hue_recommendation": hue_recommendation,
                            "title_recommendation": title_recommendation
                        }
                        st.session_state["all_result"].append(resp)

                        print("Summary results: \n", resp)

                    st.session_state[index_past].append(new_question)
                    output_template = f"""
                    {output} \n\n Query:\n{query_recommendation}
                    """

                    st.session_state[index_generated].append(output_template)


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
            if chart_recommendation != None:
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

                if "scatter" in chart_recommendation.lower():

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
                            dashboard.Item(item_key, 0, counter_recommendation, 4, 3, isResizable=True, isDraggable=True)
                        ]
                    counter_recommendation += 1

                if 'box' in chart_recommendation.lower() or 'swarm' in chart_recommendation.lower():

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
                            dashboard.Item(item_key, 0, counter_recommendation, 4, 3, isResizable=True, isDraggable=True)
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
            index_question_counter = 0
            for recommendation in st.session_state["all_result"]:
                query_recommendation = recommendation['query_recommendation']
                question = recommendation['question']
                x_recommendation = recommendation['x_recommendation']
                y_recommendation = recommendation['y_recommendation']
                hue_recommendation = recommendation['hue_recommendation']
                chart_recommendation = recommendation['chart_recommendation']
                title_recommendation = recommendation['title_recommendation']
                item_key = "item_" + str(question)

                # Get new dataframe
                dataframe_new = get_dataframe_from_duckdb_query(query_recommendation)
                mui_card_style= {"color": '#555', 'bgcolor': '#f5f5f5', "display": "flex", 'borderRadius': 1,  "flexDirection": "column"}

                if "bar" in chart_recommendation.lower():
                    if (x_recommendation != 'None') & (y_recommendation != 'None'):
                        with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                            plot.create_bar_chart(dataframe_new, x_recommendation, y_recommendation, hue_recommendation, title_recommendation)

                elif "metric" in chart_recommendation.lower():
                    with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                        plot.create_metric_chart(dataframe_new, x_recommendation, y_recommendation,title_recommendation)
                        # mui.IconButton(mui.icon.Close,
                        #                sx={
                        #                    "position": 'absolute',
                        #                    "zIndex": "tooltip",
                        #                    "top": -7,
                        #                    "left": '95%',
                        #                    "maxWidth": '15px',
                        #                    "maxHeight": '15px',
                        #                    "minWidth": '15px',
                        #                    "minHeight": '15px'
                        #                }, fontSize="inherit",
                        #                   disableElevation=True,
                        #                   variant="text",
                        #                onClick=delete_session_from_cache)

                elif "scatter" in chart_recommendation.lower():
                    if (x_recommendation != 'None') & (y_recommendation != 'None'):
                        with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                            plot.create_scatter_plot(dataframe_new, x_recommendation, y_recommendation,hue_recommendation, title_recommendation)

                elif 'box' in chart_recommendation.lower() or 'swarm' in chart_recommendation.lower():
                    if (x_recommendation != 'None') & (y_recommendation != 'None'):
                        with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                            plot.create_swarm_plot(dataframe_new, x_recommendation, y_recommendation,hue_recommendation, title_recommendation)

                index_question_counter+=1

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
                        height_adjustor = len((st.session_state[index_generated][i]).strip())*0.5
                        st.text_area(label = "Answer🤖", value = (st.session_state[index_generated][i]).strip(), disabled=True,
                                     height=int(height_adjustor))
                        counter_message_limit += 1
                except:
                    pass


if UPLOADED_FILE is not None:
    # Create a text element and let the reader know the data is loading.
    DATA, sample_data_overview = load_data(UPLOADED_FILE)

    ##################################################
    with st.expander("See data explaination"):
        get_data_overview(sample_data_overview)

    # Inspecting raw data
    with st.expander("See raw data"):
        get_raw_table(DATA)

    # Inspecting summary statistics
    with st.expander("See summary statistics"):
        get_summary_statistics(DATA)

    data_schema = convert_datatype(DATA)
    schema_data = str(data_schema.dtypes.to_dict().items())

    st.markdown("### AIViz💬")
    st.write("List of sample questions")
    col1, col2, col3, col4, col5 = st.columns(5)

    # Generate 5 sample questions
    sample_question_1, sample_question_2, sample_question_3, sample_question_4, sample_question_5 = create_sample_question(schema_data, DATA)
    # sample_question_1 = "What us the average age of the people in the dataset?"
    # sample_question_2 = "What is the most common sex in the dataset?"
    # sample_question_3 = "What is the average BMI of the people in the dataset?"
    # sample_question_4 = "What is the average number of children in the dataset?"
    # sample_question_5 = "What is the most common region in the dataset?"
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








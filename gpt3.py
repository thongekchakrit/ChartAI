import openai
import streamlit as st
import duckdb
import re
import numpy as np
import random

def gpt_promt(message):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": "You are an actuary."},
            {"role": "user", "content": message},
        ])
    return response.choices[0]['message']

def gpt_promt_davinci(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=message,
        temperature=0.01,
        max_tokens=1000)
    return response.choices[0]['text']

@st.cache_data(show_spinner=False)
def create_sample_question(schema_data, data, regenerate_new_question):

    summary_statistics = data.describe()
    corr_data = data.corr()

    goals_sample_question = re.findall(r"<goal_start>(.*)<goal_end>", regenerate_new_question.replace("\n", ' '))

    if len(goals_sample_question) > 0:
        prompt = f"You are an data analyst, " \
                 f"Generate me 50 questions based on data using the schema {schema_data}, use " \
                 f"summary statistics: {summary_statistics} and" \
                 f"correlation statistics: {corr_data}. to generate more questions" \
                 f"please generate the questions to meet the objective of {goals_sample_question}" \
                 f"Put each question in <question_start> your generated question <question_end>."
    else:
        prompt = f"You are an data analyst, " \
                 f"Generate me 50 questions based on data using the schema {schema_data}, use " \
                 f"summary statistics: {summary_statistics} and" \
                 f"correlation statistics: {corr_data}. to generate more questions" \
                 f"Put each question in <question_start> your generated question <question_end>."

    response = gpt_promt_davinci(prompt)

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

    # print(f"Number of question generated: {regenerate_new_question}")
    return question_1, question_2, question_3, question_4, question_5

@st.cache_data(show_spinner=False)
def query(sample_data_overview, new_question):
    prompt = f"You are an actuary, " \
             f"Given the csv file sample data with headers: {sample_data_overview}, " \
             f"write a sql script with given dataset columns to get '{new_question}'. " \
             f"What plot can best represent this data?"
    response = gpt_promt_davinci(prompt)
    query = response.replace("sample_data", "DATA")
    query = query.replace("\n", " ")
    dataframe_new = duckdb.query(query).df()
    st.session_state['question_dict_dataset input analysis - visuals'][new_question] = dataframe_new
    return response

@st.cache_data(show_spinner=False)
def generate_sql_gpt(_data_schema, new_question, _sample_data):
    prompt = f"""
    
    Example Context: 
    You are a data analyst
    Given the data with schema:
    dict_items([('key', string[python]), ('author', string[python]), ('date', dtype('<M8[ns]')), ('stars', Int64Dtype()), ('title', string[python]), ('helpful_yes', Int64Dtype()), ('helpful_no', Int64Dtype()), ('text', string[python])])
    
    Example Question: 
    Write me an  SQL script in duckDB language that can answer the following question: "How many authors are there in the year 2022?". 
    Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. 
    Please give column names after the transformation and select an appropriate number of columns so that we can create a visualization from it.
    For bar chart, swarm plot, box plot, please make sure to include 3 columns.
    Please convert all result to lower case.
    
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
    For bar chart, swarm plot, box plot, please make sure to include 3 columns.
    If correlation or corr or percentile is asked and one of the variable schema is string. Convert it into integer using one-hot encoding.
    
    Answer: 
    <sql_start>
    SELECT CORR(charges, bmi) as correlation 
    FROM DATA
    <sql_end>
    
    Context: 
    You are a data analyst
    Given the data with schema: 
    {_data_schema}
    Given sample data:
    {_sample_data}
    
    Question: 
    Write me an SQL script in duckDB language that can answer the following question:  {new_question}
    Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. 
    Please give column names after the transformation and select an appropriate number of columns so that we can create a visualization from it.
    For bar chart, swarm plot, box plot, please make sure to include 3 columns.
    Please convert all result to lower case.
    
    """

    # print(prompt)
    # print("\n")

    response = gpt_promt_davinci(prompt)
    try:
        query_recommendation = re.search(r"<sql_start>(.*)<sql_end>", response.replace("\n", ' ')).group(1).strip()
    except:
        query_recommendation = None

    print(query_recommendation)

    return query_recommendation


@st.cache_data(show_spinner=False)
def query_chart_recommendation(_data_schema, new_question, recommened_query, number_of_records, _sample_data):
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
        
        Bar Chart, Scatter plot, swarm plot must have recommended hue.
        Recommend the x and y variables for the plot based on the query and schema provided.
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
        
        Bar Chart, Scatter plot, swarm plot must have recommended hue.
        Recommend the x and y variables for the plot based on the query and schema provided.
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
        
        Bar Chart, Scatter plot, swarm plot must have recommended hue.
        Recommend the x and y variables for the plot based on the query and schema provided.
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
        
        Sample Data: {_sample_data}

        Based on the question: {new_question} and the query above, 
        recommend me a graph that can be used to best represent the question and the SQL generated.
        If total records is 1 and sql query has 1 column, recommend metric plot and recommended x variable.
        Put the recommended chart in the tag "<chart_start>" and end with "<chart_end>".
        
        Bar Chart, Scatter plot, swarm plot must have recommended hue.
        Recommend the x and y variables for the plot based on the query and schema provided.
        Put the recommendated x in the tag "<x_var_start>" and "<x_var_end>".
        y in the tag "<y_var_start>" and "<y_var_end>" .
        hue/class in "<hue_var_start>" and "<hue_var_end>".
        Put numerical value for x and y. categorical value in hue.

        Give an appropriate title. Put the title in the tag "<title_start>" and "<title_end>"

        """

    response = gpt_promt_davinci(prompt)

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

    print(chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation)

    return chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation

@st.cache_data(show_spinner=False)
def query_no_result(_sample_data_overview, new_question, sql_query):

    prompt = f"You are an analyst, " \
             f"Given the data with schema: {_sample_data_overview}, " \
             f"you have generated no result for the question '{new_question}'. " \
             f"using the sql query '{sql_query}'. " \
             f"explain why no result was returned." \
             f"Do not show the query in the answer."
    response = gpt_promt_davinci(prompt)
    return response

@st.cache_data(show_spinner=False)
def recursion_batch(list_of_df, list_of_result, new_question, query_recommendation):
    '''
    :param query_recommendation: The query that was created by GPT3 API
    :param new_question: The question that was asked by the user
    :param dataframe_new: The dataframe that was created in DuckDB with the query generated by GPT3
    :param list_of_result: Empty list to store the result from chat gpt
    :return: Recursive response from chat GPT
    '''

    # print("Recursive batch length: ", len(list_of_df[0].to_json()))
    # print("Recursive batch: ", list_of_df[0])
    # print("Length: ", len(list_of_result))
    # print("Content: ", list_of_result)
    if len(list_of_df) <= 10:
        if len(list_of_df) < 2:
            dataframe_json = list_of_df[0].to_json()
            prompt = f"You are an analyst, " \
                     f"Please give a report and insights of the result in human readable text: " \
                     f"The question '{new_question}' was asked. The result has been generated using {query_recommendation}," \
                     f"Answering in a way that answers the question, explain the result: {dataframe_json}" \
                     f"Do not show the query in the answer."
            list_of_result = list_of_result + [gpt_promt_davinci(prompt)]
            return list_of_result
        else:
            dataframe_json = list_of_df[0].to_json()
            prompt = f"You are an analyst, " \
                     f"Please give a report and insights of the result in human readable text: " \
                     f"The question '{new_question}' was asked. The result has been generated using {query_recommendation}," \
                     f"Answering in a way that answers the question, explain the result: {dataframe_json}" \
                     f"Do not show the query in the answer."
            list_of_result = list_of_result + [gpt_promt_davinci(prompt)]
            new_list = list_of_df[1:]
            return recursion_batch(new_list, list_of_result, new_question, query_recommendation)
    else:
        st.error('Performing huge data set analysis is disabled for now...')
        return "Sorry, we've disabled huge processing of large file insights for now..."

@st.cache_data(show_spinner=False)
def recursive_summarizer_sub(list_of_response, list_of_result_response, new_question):

    if len(list_of_response) < 2:
        list_of_result_response = list_of_result_response + list_of_response
        return list_of_result_response
    else:
        data = '\n'.join(list_of_response[0])
        prompt = f"Given the question is {new_question}." \
                 f"Summarize the following text after: {data}"
        list_of_result_response = list_of_result_response + [gpt_promt_davinci(prompt)]
        new_list = list_of_response[1:]
        return recursive_summarizer_sub(new_list, list_of_result_response, new_question)

@st.cache_data(show_spinner=False)
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

@st.cache_data(show_spinner=False)
def explain_result(query_recommendation, new_question, dataframe_new):

    print("len(dataframe_new.to_json()): ", len(dataframe_new.to_json()))
    ratio_character = len(dataframe_new.to_json())/ 3200
    is_modulo = len(dataframe_new.to_json()) % 3200 > 0
    print(len(dataframe_new.to_json()) % 3200 > 0 )
    if ratio_character < 1:
        batch_size = 1
    else:
        batch_size = round(ratio_character + is_modulo)
    print(f"Batch size: {batch_size}")
    list_of_df = np.array_split(dataframe_new, batch_size)
    # sample data to first 10 dataframe to get result, to remove in prod
    list_of_df = list_of_df[:3]
    list_of_result = []
    for col, dtype in dataframe_new.dtypes.items():
        if 'datetime' in str(dtype):
            dataframe_new[col] = dataframe_new[col].dt.strftime('%Y-%m-%d')
            dataframe_new = dataframe_new.sort_values(by=[col])

    response = recursion_batch(list_of_df, list_of_result, new_question, query_recommendation)

    if response:
        list_of_result_response = []
        st.success('Done!')
        if len(response) >= 2:
            # print("Processing sub explaination")
            max_words_per_list = 3500
            sublists = split_words_into_sublists(response, max_words_per_list)
            # print("Sublist of result: ", sublists)
            response = recursive_summarizer_sub(sublists, list_of_result_response, new_question)
            response = '\n'.join(response)
        else:
            # print("Combining the response")
            response = '\n'.join(response)

    return response


# def recursive_summarizer_main(response, list_of_response, new_question):
#     if len(response) < 2:
#         return response[0]
#     else:
#         list_of_summarize_text = []
#         response = recursive_summarizer_sub(response, list_of_summarize_text, new_question)
#         return recursive_summarizer_main(response, list_of_response, new_question)



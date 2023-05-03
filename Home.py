import streamlit as st
from streamlit_elements import elements, mui
from streamlit_elements import dashboard
from pandas.errors import ParserError
from streamlit_chat import message
import streamlit_toggle as tog
import pandas as pd
import json
import gpt3 as open_ai_gpt3
import duckdb
import plot
import re
import os

# if authentication_status:
st.set_page_config(page_title="ChartAI", page_icon="assets/images/favicon.png", layout="wide", initial_sidebar_state='collapsed')
col_main_1, col_main_2, col_main_3 = st.columns([1,5,1])

with col_main_2:
    st.markdown("# **ChartAI - Text to Graphs/Charts**")
    st.markdown(
        """
        Generate insights and graphs from raw data in this web application.  
        Try out our application’s functions with our sample dataset below,  
        or simply upload your csv file and explore your data using natural language.  
        """
    )
    UPLOADED_FILE = st.file_uploader("Upload your data")

hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


GPT_SECRETS = st.secrets["gpt_secret"]
SIDE_BAR_QUESTION_TAB_1 = 'question_dict_normal'
SIDE_BAR_GENERATED_DATASET_INPUT_1 = 'generated_normal'
SIDE_BAR_PAST_DATASET_INPUT_1 = 'past_normal'
open_ai_gpt3.openai.api_key = GPT_SECRETS

with col_main_2:
    if not UPLOADED_FILE:
        UPLOADED_FILE = "archive/views/sample_data_2.csv"
        st.markdown("*Application is currently running the sample dataset. To get insights from your own data, please upload your csv file.*")

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

if "all_result_hidden" not in st.session_state:
    st.session_state["all_result_hidden"] = []

if 'question_dict' not in st.session_state:
    st.session_state['question_dict'] = {}

if 'sample_question_generation' not in st.session_state:
    st.session_state['sample_question_generation'] = 0

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

@st.cache_data(show_spinner=False)
def rename_dataset_columns(dataframe):
    dataframe.columns = dataframe.columns.str.replace('[#,@,&,$,(,)]', '')
    dataframe.columns = [re.sub(r'%|_%', '_percentage', x) for x in dataframe.columns]
    dataframe.columns = dataframe.columns.str.replace(' ', '_')
    dataframe.columns = [x.lstrip('_') for x in dataframe.columns]
    dataframe.columns = [x.strip() for x in dataframe.columns]
    return dataframe

@st.cache_data(show_spinner=False)
def convert_datatype(df):
    """Automatically detect and convert (in place!) each
    dataframe column of datatype 'object' to a datetime just
    when ALL of its non-NaN values can be successfully parsed
    by pd.to_datetime().  Also returns a ref. to df for
    convenient use in an expression.
    """
    for c in df.columns[df.dtypes=='object']:
        try:
            df[c]=pd.to_datetime(df[c])
        except (ParserError,ValueError):
            df[c] = df[c].apply(str.lower)

    df = df.convert_dtypes()
    return df

@st.cache_data(show_spinner=False)
def get_raw_table(data):
    st.write(data)

@st.cache_data(show_spinner=False)
def check_data_have_object(data):
    resp = data.dtypes.to_list()
    return resp

@st.cache_data(show_spinner=False)
def get_data_overview(header):
    prompt =  f"Format your answer to markdown latex. Use markdown font size 3. " \
              f"Please do not include heading or subheading." \
              f"Given the csv file with headers: {header} " \
              f"You are an actuary, " \
              f"Describe what each column means and what the dataset can be used for?"

    response = open_ai_gpt3.gpt_promt(prompt)
    st.markdown(response['content'])

@st.cache_data(show_spinner=False)
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
        response = open_ai_gpt3.gpt_promt(prompt)
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
        response = open_ai_gpt3.gpt_promt(prompt_2)
        st.markdown(response['content'])

@st.cache_data(show_spinner=False)
def get_dataframe_from_duckdb_query(query):
    try:
        dataframe_new = duckdb.query(query).df()
    except Exception as e:
        prompt = f"""
        This SQL query: {query}
        
        Is giving an error: {e}
        
        What should be the correct SQL query?
        Put the SQL script in the tag "<sql_start>"  and end with <sql_end> for easy regex extraction. 
        Please give column names after the transformation and select an appropriate number of columns so that we can create a visualization from it.
        Please convert all result to lower case.
        """
        response = open_ai_gpt3.gpt_promt_davinci(prompt)
        try:
            query = re.search(r"<sql_start>(.*)<sql_end>", response.replace("\n", ' ')).group(1).strip()
            dataframe_new = duckdb.query(query).df()
        except:
            dataframe_new = pd.DataFrame()
    # print(dataframe_new)
    return dataframe_new, query

@st.cache_data(show_spinner=False)
def query_text(_schema_data, new_question, _sample_data):
    # print("Querying the GPT...")
    # Get the query
    query_recommendation = re.sub(" +", " ", open_ai_gpt3.generate_sql_gpt(schema_data, new_question, _sample_data))
    # Create the new dataframe
    dataframe_new, query_recommendation = get_dataframe_from_duckdb_query(query_recommendation)
    batch_size = round(len(dataframe_new.to_json())/ 3200 ) + (len(dataframe_new.to_json()) % 3200 > 0)
    schema_data_new = str(dataframe_new.dtypes.to_dict().items())
    print("Batch size: ", batch_size)
    print(dataframe_new)
    print("Shape: ", dataframe_new)
    print("\n")
    if len(dataframe_new) > 5:
        sample_data_new = dataframe_new.sample(n=5)
    else:
        sample_data_new = dataframe_new
    chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation = open_ai_gpt3.query_chart_recommendation(schema_data_new, new_question, query_recommendation, len(dataframe_new), sample_data_new)

    if len(dataframe_new) > 0:
        pass
        response = open_ai_gpt3.explain_result(query_recommendation, new_question, dataframe_new)
        print("Response", response)
    else:
        response = open_ai_gpt3.query_no_result(_schema_data, new_question, query_recommendation)
        chart_recommendation = None
        x_recommendation = None
        y_recommendation = None
        hue_recommendation = None
        title_recommendation = None

    return response, chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation, query_recommendation

@st.cache_data(show_spinner=False)
def get_raw_table(data):
    st.write(data)

@st.cache_data(show_spinner=False)
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
        with open("../session_layout/layout.json", "w") as outfile:
            outfile.write(json.dumps(data, indent=4))

    # print("check", layout_file)
    if len(layout_file) > 0:
        user_layout = layout_file[username]
    else:
        user_layout = []

    return user_layout

def show_dashboard(session_all_result, index_question_counter):
    for recommendation in session_all_result:
        if recommendation['hide_graph'] == False:
            query_recommendation = recommendation['query_recommendation']
            question = recommendation['question']
            x_recommendation = recommendation['x_recommendation']
            y_recommendation = recommendation['y_recommendation']
            hue_recommendation = recommendation['hue_recommendation']
            chart_recommendation = recommendation['chart_recommendation']
            title_recommendation = recommendation['title_recommendation']
            item_key = "item_" + str(question)

            # Get new dataframe
            dataframe_new, query_recommendation  = get_dataframe_from_duckdb_query(query_recommendation)
            mui_card_style= {"color": '#555', 'bgcolor': '#f5f5f5', "display": "flex", 'borderRadius': 1,  "flexDirection": "column"}

            if "bar" in chart_recommendation.lower():
                if (x_recommendation != 'None') & (y_recommendation != 'None'):
                    with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                        try:
                            if len(dataframe_new) <= 0:
                                raise
                            plot.create_bar_chart(dataframe_new, x_recommendation, y_recommendation, hue_recommendation, title_recommendation)
                        except:
                            plot.create_error_plot()

            elif "metric" in chart_recommendation.lower():
                with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                    try:
                        if len(dataframe_new) <= 0:
                            raise
                        plot.create_metric_chart(dataframe_new, x_recommendation, y_recommendation,title_recommendation)
                    except:
                        plot.create_error_plot()

            elif "scatter" in chart_recommendation.lower():
                if (x_recommendation != 'None') & (y_recommendation != 'None'):
                    with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                        try:
                            if len(dataframe_new) <= 0:
                                raise
                            plot.create_scatter_plot(dataframe_new, x_recommendation, y_recommendation,hue_recommendation, title_recommendation)
                        except:
                            plot.create_error_plot()

            elif 'swarm' in chart_recommendation.lower():
                if (x_recommendation != 'None') & (y_recommendation != 'None'):
                    with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                        try:
                            if len(dataframe_new) <= 0:
                                raise
                            plot.create_swarm_plot(dataframe_new, x_recommendation, y_recommendation,hue_recommendation, title_recommendation)
                        except:
                            plot.create_error_plot()

            # elif 'box' in chart_recommendation.lower():
            #     if (x_recommendation != 'None') & (y_recommendation != 'None'):
            #         with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
            #             try:
            #                 if len(dataframe_new) <= 0:
            #                     raise
            #                 plot.create_box_plot(dataframe_new, x_recommendation, y_recommendation,hue_recommendation, title_recommendation)
            #             except:
            #                 plot.create_error_plot()

            elif 'pie' in chart_recommendation.lower():
                if (x_recommendation != 'None') & (y_recommendation != 'None'):
                    with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                        try:
                            if len(dataframe_new) <= 0:
                                raise
                            plot.create_pie_chart(dataframe_new,  x_recommendation, y_recommendation,hue_recommendation, title_recommendation)
                        except:
                            plot.create_error_plot()

            elif 'line' in chart_recommendation.lower():
                if (x_recommendation != 'None') & (y_recommendation != 'None'):
                    with mui.Paper(label=question, elevation=10, variant="outlined", square=True, key=item_key, sx=mui_card_style):
                        try:
                            if len(dataframe_new) <= 0:
                                raise
                            print("Creating line plot")
                            plot.create_line_chart(dataframe_new,  x_recommendation, y_recommendation,hue_recommendation, title_recommendation)
                        except Exception as e:
                            print(e)
                            print("Creating line plot Error")
                            plot.create_error_plot()

            index_question_counter+=1

def show_messages(_index_generated, _index_past, _i, is_result):

    with st.expander(f"{str(_i+1)}.{st.session_state[_index_past][_i]}"):
        if is_result:
            message((st.session_state[_index_generated][_i]).strip(), key=str(_i), avatar_style="thumbs", seed="Mimi")
        else:
            message("The query produce no result, please rephrase the question.", key=str(_i), avatar_style="thumbs", seed="Mimi")
        message(st.session_state[_index_past][_i], is_user=True, key=str(_i) + '_user', avatar_style="thumbs", seed="Mia")
        key_build = str(st.session_state[_index_past][_i] + '_toggle_graph')
        index_q = next((index for (index, d) in enumerate(st.session_state["all_result"]) if d["question"] == st.session_state[_index_past][_i]), None)

        if tog.st_toggle_switch(label=f"Hide Graph", key=key_build, default_value=st.session_state["all_result"][index_q]['hide_graph'],
                                label_after = False, inactive_color = '#D3D3D3', active_color="#11567f",
                                track_color="#29B5E8"):
            # Move the question from key into hidden list if toggle is on
            st.session_state["all_result"][index_q]['hide_graph'] = True
        else:
            st.session_state["all_result"][index_q]['hide_graph'] = False

def ask_new_question(sample_question, schema_data, sample_data):
    key_type = 'normal'
    index_questions = 'question_dict_' + key_type
    index_generated = 'generated_' + key_type
    index_past = 'past_' + key_type

    form = st.form('user_form', clear_on_submit = True)
    if sample_question:
        new_question = form.text_area("Typing in your own question below...👇", value= sample_question, key = key_type, label_visibility="collapsed").strip().lower()
        submit_label = "Clear"
    else:
        new_question = form.text_area("Typing in your own question below...👇", key = key_type, label_visibility="collapsed").strip().lower()
        submit_label = "Submit"

    submit_button = form.form_submit_button(label=submit_label)

    chat_col, dashboard_col = st.tabs(["Textual View", "Graphical View"])

    with st.spinner("Analysing data..."):
        if (submit_button) or (sample_question):
            if new_question:
                if new_question not in st.session_state[index_questions]:
                    st.session_state[index_questions][new_question] = ''
                    for key in st.session_state[index_questions]:
                        if new_question == key:

                            output, chart_recommendation, x_recommendation, y_recommendation, hue_recommendation, title_recommendation, query_recommendation = query_text(schema_data, key, sample_data)

                            if chart_recommendation != None:
                                resp = {
                                    "question": new_question,
                                    "query_recommendation": query_recommendation,
                                    "chart_recommendation": chart_recommendation,
                                    "x_recommendation": x_recommendation,
                                    "y_recommendation": y_recommendation,
                                    "hue_recommendation": hue_recommendation,
                                    "title_recommendation": title_recommendation,
                                    "hide_graph": False
                                }
                                # Store the results of the questions
                                st.session_state["all_result"].append(resp)

                                print("Summary results: \n", resp)

                            # Store the question that was asked into past question index
                            st.session_state[index_past].append(new_question)
                            output_template = f"""
                            {output} \n\n Query:\n{query_recommendation}
                            """

                            st.session_state[index_generated].append(output_template)


                else:
                    st.info('Question exists, bringing question to recent view...', icon="⚠️")
                    exist_question_index = st.session_state[index_past].index(new_question)
                    exist_question = st.session_state[index_past].pop(exist_question_index)
                    # print(f"This question exists: {exist_question}")
                    exist_output = st.session_state[index_generated].pop(exist_question_index)
                    # print(f"This output exists: {exist_output}")

                    # Reinsert the question and output
                    st.session_state[index_past].append(exist_question)
                    st.session_state[index_generated].append(exist_output)

        #########################################################################################################################
        ## Populating the question and answers
        #########################################################################################################################
        with chat_col:
            if st.session_state["all_result"]:
                st.markdown("### Answers")
                counter_non_result = 0
                counter_message_limit = 0
                if st.session_state[index_generated]:
                    placeholder = st.empty()
                    with placeholder.container():
                        total_length_reverse =  reversed(range(len(st.session_state[index_generated])-1, -1, -1))
                        for i in total_length_reverse:
                            try:
                                if (st.session_state[index_generated][i]).strip() == "The query produce no result, please rephrase the question.":
                                    counter_non_result += 1
                                    if counter_non_result <= 1:
                                        # if questions does not produce result,
                                        # only show the first question and hide the rest
                                        show_messages(index_generated, index_past, i, False)

                                else:
                                    # Show the lastest 5 message
                                    # if questions have result print them out
                                    show_messages(index_generated, index_past, i, True)
                                    counter_message_limit += 1
                            except:
                                pass

        #########################################################################################################################
        ## Handling the Dashboard Layouts For Created Charts
        #########################################################################################################################
        # Create a list to keep the layout
        layout = []
        # Plot element dashboard
        with dashboard_col:
            with elements("dashboard"):

                # initialize layout
                # check_layout_user_exists(username)
                counter_recommendation = 0

                # Check if session state have a chart
                if 'streamlit_elements.core.frame.elements_frame.dashboard' in st.session_state:
                    if st.session_state['streamlit_elements.core.frame.elements_frame.dashboard']:
                        session_state_layout = json.loads(st.session_state['streamlit_elements.core.frame.elements_frame.dashboard'])
                        if 'streamlit_elements.core.frame.elements_frame.dashboard00000000' in session_state_layout:
                            layout = session_state_layout['streamlit_elements.core.frame.elements_frame.dashboard00000000']['updated_layout']
                    # print("============================================================================")

                # You can create a draggable and resizable dashboard using
                for recommendation in st.session_state["all_result"]:
                    if recommendation['hide_graph'] == False:
                        question = recommendation['question']
                        chart_recommendation = recommendation['chart_recommendation']
                        if chart_recommendation != None:
                            if 'pie' in chart_recommendation.lower():
                                width = 4
                                height = 2
                            elif 'line' in chart_recommendation.lower():
                                width = 6
                                height = 2
                            elif 'metric' in chart_recommendation.lower():
                                width = 2
                                height = 1
                            elif 'bar' in chart_recommendation.lower():
                                width = 6
                                height = 3
                            elif 'box' in chart_recommendation.lower():
                                width = 4
                                height = 2
                            else:
                                width = 3
                                height = 2
                            # First, build a default layout for every element you want to include in your dashboard
                            item_key = "item_" + str(question)

                            if len(layout) > 0:
                                for layer in layout:
                                    if layer['i'] == item_key:
                                        pass
                                    elif item_key not in str(layout):
                                        layout = layout + [
                                            # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
                                            dashboard.Item(item_key, 0, counter_recommendation, width, height, isResizable=True, isDraggable=True)
                                        ]
                                    else:
                                        pass
                            else:
                                layout = layout + [
                                    # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
                                    dashboard.Item(item_key, 0, counter_recommendation, width, height, isResizable=True, isDraggable=True)
                                ]
                            counter_recommendation += 1
                def handle_layout_change(updated_layout):
                    print("\n")

                #########################################################################################################################
                ## Handling the Dashboard
                #########################################################################################################################
                if st.session_state["all_result"]:
                    st.markdown("### Dashboard")
                with dashboard.Grid(layout, onLayoutChange=handle_layout_change):
                    index_question_counter = 0
                    show_dashboard(st.session_state["all_result"], index_question_counter)

#########################################################################################################################
## Main Application
#########################################################################################################################

if UPLOADED_FILE is not None:
    # Create a text element and let the reader know the data is loading.
    DATA, sample_data_overview = load_data(UPLOADED_FILE)

    #################################################
    with col_main_2:
        st.markdown("### Data Explanation 🔎")
        st.markdown("The topic below gives you a general feel of the dataset, click on the expander to see more.")
        with st.expander("See data explanation"):
            get_data_overview(sample_data_overview)

        # Inspecting raw data
        with st.expander("See raw data"):
            get_raw_table(DATA)

        # Inspecting summary statistics
        # with st.expander("See summary statistics"):
        #     get_summary_statistics(DATA)

        data_schema = convert_datatype(DATA)
        schema_data = str(data_schema.dtypes.to_dict().items())
        sample_data = str(DATA.sample(n=3).to_dict().items())

        st.markdown("### Exploration 💬")
        st.write("Below are some sample questions, pick one of the questions below to see how our AI can analyse your question.")
        col1, col2, col3, col4, col5 = st.columns(5)
        col_question_1, col_question_2 = st.columns([1, 2])

        # Check if Button is pressed
        regenerate_new_question = 'None'

        # Generate 5 sample questions
        with col_question_1:
            if st.button('🔄 Re-generate sample question'):
                new_sample_question = st.session_state['sample_question_generation']
                st.session_state['sample_question_generation'] = new_sample_question+1
                regenerate_new_question = "regenerate_sample_question" + str(st.session_state['sample_question_generation'])

        sample_question_1, sample_question_2, sample_question_3, sample_question_4, sample_question_5 = open_ai_gpt3.create_sample_question(schema_data, DATA, regenerate_new_question)
        question = None

        # Create the sample questions columns
        with col1:
            if st.button(sample_question_1):
                question = sample_question_1.lower()

        with col2:
            if st.button(sample_question_2):
                question = sample_question_2.lower()

        with col3:
            if st.button(sample_question_3):
                question = sample_question_3.lower()

        with col4:
            if st.button(sample_question_4):
                question = sample_question_4.lower()

        with col5:
            if st.button(sample_question_5):
                question = sample_question_5.lower()

        # Generate the ask question bar
        st.markdown("Type in your question below (Press Ctrl+Enter to key in question):")
        ask_new_question(question, schema_data, sample_data)

    st.markdown(
        """
        <style>
            
            .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f8f8f8;
            color: #999999;
            text-align: center;
            padding: 10px;
            }
            
            .footer a {
            align-items: center;
            justify-content: center;
            height: 100%;
            margin: 0 10px;
            opacity: 0.8;
            transition: opacity 0.3s ease-in-out;
            font-co
            }
            
            .footer a:hover  {
                opacity: 0.5;
            }
        </style>
        
        <div class="footer">
            <a href="https://www.linkedin.com/in/thongekchakrit/">LinkedIn</a>
            <a href="./Privacy_Policy">Privacy Policy</a>
            <a href="./Feature_Release">Feature Release</a>
            version 0.0.1 (pre-alpha)
            
        </div>""",
        unsafe_allow_html=True)
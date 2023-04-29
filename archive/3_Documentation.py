import streamlit as st
st.set_page_config(page_icon="assets/images/favicon.png")
col_main_1, col_main_2, col_main_3 = st.columns([1,4,1])

hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)


st.markdown("""
# Quickstart Guide
This tutorial gives you a quick walkthrough about the use of our application, and the most common frequently asked questions.

## Coming Soon...

""")

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
    Made By Chakrit Thong EK: &nbsp;
        <a href="https://github.com/thongekchakrit">GitHub</a>
        <a href="https://www.linkedin.com/in/thongekchakrit/">LinkedIn</a>
        <a href="./Privacy_Policy">Privacy Policy</a>
        <a href="./Documentation">Documentation</a>
        <a href="./Feature_Release">Feature Release</a>
        
    </div>""",
    unsafe_allow_html=True,
)
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
# Privacy Policy
Thank you for using our website. We understand the importance of your privacy and are committed to protecting your personal information. This privacy policy outlines how we collect, use, and disclose information about our users.

## Collection of Information
We do not collect any personal information about our users unless they voluntarily provide it to us. The only information we collect is the CSV file that the user uploads to our website. This file is used in the session only and will not be saved once the user exits the site. We do not collect or store any other information about our users.

## Use of Information
The CSV file uploaded by the user is used solely for the purpose of generating a report. We do not use this information for any other purpose or share it with any third-party organizations. Please note that we also use the GPT-3 API for data analysis, GPT-3 API does not, and we do not store any information received from the GPT-3 API.
## Disclosure of Information
We do not disclose any personal information about our users to third-party organizations. We only use the CSV file uploaded by the user for generating a report, and this file is not shared with anyone else.

## Security
We take the security of our users' information very seriously. We use industry-standard measures to protect the information that is stored on our website, including encryption and firewalls. We regularly monitor our systems for any vulnerabilities or threats to ensure that our users' information remains secure.

## Changes to this Privacy Policy
We reserve the right to update or modify this privacy policy at any time. Any changes we make to this policy will be posted on this page, and we encourage our users to review this page periodically to stay informed about any changes.

## Contact Information
If you have any questions or concerns about this privacy policy or our website's privacy practices, please contact us at thongekchakrit@gmail.com.

Last update: 19 April 2023
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
        <a href="https://www.linkedin.com/in/thongekchakrit/">LinkedIn</a>
        <a href="./Privacy_Policy">Privacy Policy</a>
        <a href="./Feature_Release">Feature Release</a>
        
    </div>""",
    unsafe_allow_html=True,
)
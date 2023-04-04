# import streamlit as st
# import streamlit_authenticator as stauth
# import yaml
# from yaml.loader import SafeLoader
# import utils as utl
# from views import home,home_v2, home_v3, about,configuration
#
# st.set_page_config(layout="centered", page_title='Automated Data Analysis', page_icon = 'assets/images/favicon.png')
# st.set_option('deprecation.showPyplotGlobalUse', False)
# utl.inject_custom_css()
# utl.navbar_component()
#
# def navigation():
#     route = utl.get_current_route()
#
#     # Hiding footer
#     hide_default_format = """
#                <style>
#                footer {visibility: hidden;}
#                </style>
#                """
#     st.markdown(hide_default_format, unsafe_allow_html=True)
#
#     hide_menu_style = """
#             <style>
#             #MainMenu {visibility: hidden;}
#             </style>
#             """
#     st.markdown(hide_menu_style, unsafe_allow_html=True)
#
#
#     # Login before displaying of webapp
#     with open('config.yaml') as file:
#         config = yaml.load(file, Loader=SafeLoader)
#         print(config)
#
#     authenticator = stauth.Authenticate(
#         config['credentials'],
#         config['cookie']['name'],
#         config['cookie']['key'],
#         config['cookie']['expiry_days'],
#         config['preauthorized']
#     )
#
#     name, authentication_status, username = authenticator.login('Login', 'main')
#
#     if authentication_status:
#         if route == "home":
#             home.load_view()
#         elif route == "home_v2":
#             home_v2.load_view()
#         elif route == "home_v3":
#             home_v3.load_view()
#         elif route == "about":
#             about.load_view()
#         elif route == "configuration":
#             configuration.load_view()
#         elif route == None:
#             home.load_view()
#     elif authentication_status is False:
#         st.error('Username/password is incorrect')
#     elif authentication_status is None:
#         st.warning('Please enter your username and password')
#
# navigation()
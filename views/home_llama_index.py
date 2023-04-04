# import os
#
# import streamlit as st
# from llama_index import LLMPredictor, GPTSimpleVectorIndex, PromptHelper, ServiceContext, SimpleDirectoryReader
# from langchain import OpenAI
#
# def load_view():
#     st.markdown("# **Data Analytics AI**")
#     st.markdown(
#         "Uploading a csv, ask a question and gain insights from your data."
#     )
#
#     UPLOADED_FILE = st.file_uploader("Choose a file")
#     GPT_SECRETS = st.secrets["gpt_secret"]
#     gpt3.openai.api_key = GPT_SECRETS
#
#     if UPLOADED_FILE is not None:
#         # Create a text element and let the reader know the data is loading.
#         # define LLM
#         llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="gpt-3.5-turbo", max_tokens=512)) #you can configure the max_tokens also
#
#         # define prompt helper
#         # set maximum input size
#         max_input_size = 4096
#         # set number of output tokens
#         num_output = 256
#         # set maximum chunk overlap
#         max_chunk_overlap = 20
#         prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)
#
#         service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
#
#         # documents = SimpleDirectoryReader('/data').load_data()
#         # index = GPTSimpleVectorIndex.from_documents(documents)
#         # index = GPTSimpleVectorIndex.from_documents(
#         #     documents, service_context=service_context
#         # )
#
#         # # # # save to disk
#         # index.save_to_disk('index.json')
#
#         # load from disk
#         index = GPTSimpleVectorIndex.load_from_disk('index.json')
#
#         response = index.query("Question?")
#         print(response)
#
#
#     else:
#         with st.sidebar:
#             st.markdown("# AutoViZChat💬")
#             st.text("Waiting for dataset to be uploaded...")





FROM python:latest

# Any working directory can be chosen as per choice like '/' or '/home' etc
WORKDIR /usr/

#to COPY the remote file at working directory in container
COPY . .

# install the needed files
RUN pip install -r requirements.txt

#from official image documentation
CMD ["python", "streamlit run ./main.py --server:8080"]
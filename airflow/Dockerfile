FROM apache/airflow:3.0.2

# Install required system libraries
USER root
RUN apt-get update && apt-get install -y \
    libgl1 \
    && apt-get clean

USER airflow

ADD requirements.txt .
RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt

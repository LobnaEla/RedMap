FROM apache/airflow:3.0.2

# Install required system libraries (lighter dependencies without OCR libs)
USER root
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean

USER airflow

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
# Download spaCy language model
RUN python -m spacy download en_core_web_sm

# Ensure the cti_pipeline module can be found
ENV PYTHONPATH="/opt/airflow:/opt/airflow/cti_pipeline:${PYTHONPATH}"

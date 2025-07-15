FROM apache/airflow:2.11.0

USER root

# Install Chrome and chromedriver
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl ca-certificates \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt install -y ./google-chrome-stable_current_amd64.deb \
    && rm ./google-chrome-stable_current_amd64.deb \
    && wget https://chromedriver.storage.googleapis.com/124.0.6367.91/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm chromedriver_linux64.zip

USER airflow

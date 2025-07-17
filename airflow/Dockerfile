FROM apache/airflow:2.11.0

USER root

# Install Chrome and chromedriver using Chrome for Testing API
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl ca-certificates jq \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt install -y ./google-chrome-stable_current_amd64.deb \
    && rm ./google-chrome-stable_current_amd64.deb \
    && CHROME_VERSION=$(google-chrome --version | cut -d' ' -f3) \
    && CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | jq -r ".versions[] | select(.version==\"$CHROME_VERSION\") | .downloads.chromedriver[] | select(.platform==\"linux64\") | .url") \
    && wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

USER airflow
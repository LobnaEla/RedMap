# Development Build

## Setup Build Assets

Before building, download these files to `build-assets/` folder:

```bash
mkdir -p airflow/build-assets
cd airflow/build-assets

# Download required files
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
wget https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.87/linux64/chromedriver-linux64.zip  
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
```

## Build & Run

```bash
docker compose up --build -d
```

**Note:** If you want the old method (download during build), change `dockerfile: Dockerfile.dev` to `dockerfile: Dockerfile.prod` in docker-compose.yml



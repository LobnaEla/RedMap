# MITRE ATT&CK Extractor

This script downloads the latest MITRE ATT&CK Enterprise dataset in JSON format and converts it into a CSV file.

## Features

- Fetches the latest `enterprise-attack.json` from the official MITRE CTI repository.
- Extracts and processes tactics and techniques, skipping revoked or deprecated items.
- Converts markdown-like descriptions to plain text.
- Outputs a CSV file (`enterprise-attack.csv`) with the following columns:
  - name
  - id
  - url
  - platforms
  - kill chain phases
  - description
  - data sources
  - detection

## Usage

1. Make sure you have Python 3 and the `requests` library installed:
   ```
   pip install requests
   ```

2. Run the script:
   ```
   python mitre_attack_csv.py
   ```

3. The script will generate `enterprise-attack.csv` in the current directory.

## Output

The resulting CSV file contains one row per technique, with details such as name, ID, platforms, associated tactics, data sources, detection, and description.

## License

This project is for educational and research purposes. Please refer to the MITRE ATT&CK [Terms of Use](https://attack.mitre.org/resources/terms-of-use/) for data usage guidelines.

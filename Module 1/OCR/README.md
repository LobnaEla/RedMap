# OCR Tool Library

This project provides a simple but powerful Python library for extracting and cleaning text from images of documents. It uses the **DocTR** library for high-accuracy OCR and **spaCy** for intelligent text polishing.

## Core Features

- **High-Accuracy OCR**: Leverages DocTR's pre-trained models to handle complex document layouts.
- **Intelligent Text Cleaning**: Automatically fixes common OCR errors like merged words, incorrect spacing, and formatting artifacts.
- **Simple API**: Extract text from any image with a single function call.

## Project Setup

Follow these steps to set up your environment.

### 1. Create a Virtual Environment

In the project's root directory, create a virtual environment:

```bash
python -m venv .venv
```

### 2. Activate the Virtual Environment

**On Windows:**
```bash
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Requirements

Install the necessary packages:

```bash
pip install -r requirements.txt
```

## How to Use the Library

The primary function is `extract_text` in the `ocr_library.py` module. You can import and use it in your own scripts as follows:

```python
from ocr_library import extract_text

image_path = "path/to/your/image.png"

try:
    extracted_text = extract_text(image_path)
    print("--- Extracted Text ---")
    print(extracted_text)
except FileNotFoundError as e:
    print(e)
```

## Testing Scripts

The repository also contains scripts used for development and comparison:

-   **`DocTR.py`**: A script for batch-processing a folder of images using the DocTR-based approach. This was used to validate the final library code.
-   **`PaddleOCR.py`**: An earlier implementation using PaddleOCR. This is kept for comparison but is not the recommended approach.

These scripts are for **testing and demonstration purposes only**. The core, reusable functionality is in `ocr_library.py`.

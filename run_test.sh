#!/bin/bash
# Runner script for OCR tests using the virtual environment

# Activate virtual environment
source .venv/bin/activate

# Run the test
python test_azure_native_markdown.py

# Deactivate
deactivate

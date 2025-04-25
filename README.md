# Streamlit AI Data Explorer

This Streamlit application allows users to upload CSV or XLSX files, view the data, and interact with an AI assistant (powered by OpenAI's GPT models) to ask questions about the contents of the selected dataset.

## Overview

The application provides a simple interface with three main sections:

1.  **File Upload (Sidebar):** Upload one or more CSV or XLSX files. The application automatically detects sheets within Excel files and treats each sheet as a separate DataFrame.
2.  **Data Viewer (Main Area - Left):** Select any loaded DataFrame or sheet to view its first N rows.
3.  **AI Chat (Main Area - Right):** Select a DataFrame/sheet to provide context to the AI. Ask questions about the data, and the AI will respond based on the *entire content* of the selected DataFrame sent to it.

## Features

*   **File Upload:** Supports `.csv` and `.xlsx` file formats.
*   **Multi-File/Sheet Handling:** Manages multiple uploaded files and individual sheets from Excel workbooks as distinct DataFrames.
*   **DataFrame Caching:** Uses Streamlit's caching (`@st.cache_data`) to speed up reloading of already processed files.
*   **Interactive Data Viewing:** Display the head of selected DataFrames with a configurable number of rows.
*   **AI-Powered Chat:**
    *   Utilizes OpenAI's API (specifically configured for `gpt-4-turbo` in the code).
    *   Allows selecting a specific DataFrame to set the context for the chat.
    *   Sends the **full content** of the selected DataFrame (converted to Markdown) to the AI model for comprehensive analysis.
    *   Displays chat history for the current session.
    *   Includes basic user feedback buttons (currently logs to `st.toast`).

## Tech Stack

*   **UI Framework:** Streamlit
*   **Data Handling:** Pandas
*   **AI Integration:** OpenAI Python Library
*   **Language:** Python

## Setup and Installation

1.  **Clone the repository (or save the code):**
    ```bash
    # git clone https://github.com/zekaistic/Cyber-Sierra-Challenge.git
    # cd Cyber-Sierra-Challenge

    # Or just save the Python script (e.g., as app.py)
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    streamlit
    pandas
    openai
    openpyxl # Required by pandas for reading .xlsx files
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

**OpenAI API Key:**

You **MUST** configure your OpenAI API key. The current code has a placeholder:

```python
OPENAI_API_KEY = "" # Replace w key to use

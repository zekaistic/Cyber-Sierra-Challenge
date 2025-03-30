import streamlit as st
import pandas as pd
import openai
import os
from io import StringIO, BytesIO
import time 

OPENAI_API_KEY = "" # Replace w key to use

if not OPENAI_API_KEY:
    st.error(
        "OpenAI API key not found."
    )
    st.stop()
else:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.error(
            f"Error configuring OpenAI client: {e}. "
        )
        st.stop()

# Initialising variables such that even when Streamlit reruns, the variables are not lost
if "messages" not in st.session_state:
    st.session_state.messages = [] # to store chat history
if "uploaded_files_info" not in st.session_state:
    st.session_state.uploaded_files_info = {} # to store uploaded files (key: filename, value: file content)
if "dataframes" not in st.session_state:
    st.session_state.dataframes = {} # to store panda dataframes (key: filename, value: dataframe)
if "selected_df_key_for_chat" not in st.session_state:
    st.session_state.selected_df_key_for_chat = None # to keep track of which dataframe is selected

# load_dataframe function
@st.cache_data(show_spinner="Loading data...") #Streamlit cache to avoid reloading dataframes
def load_dataframe(file_info, filename): # dictionary, string
    try:
        file_content = file_info["content"]
        file_type = file_info["type"]

        if file_type == "text/csv":
            stringio = StringIO(file_content.decode("utf-8"))
            df = pd.read_csv(stringio)
            return {filename: df}
        elif (
            file_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ):
            bytesio = BytesIO(file_content)
            xls = pd.ExcelFile(bytesio)
            dfs = {}
            for sheet_name in xls.sheet_names:
                df_name = f"{filename} - {sheet_name}"
                dfs[df_name] = pd.read_excel(xls, sheet_name=sheet_name)
            return dfs
        else:
            st.error(f"Unsupported file type: {file_type} for {filename}")
            return {}
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return {} # return empty dictionary to show no dataframe was loaded


# Helper function to send full DataFrame as Markdown, to be sent to AI model
def get_dataframe_context(df, df_name):
    context = f"You are analyzing the DataFrame named '{df_name}'.\n\n"
    context += "Here is the entire DataFrame content in Markdown format:\n\n```markdown\n"
    try:
        markdown_string = df.to_markdown(index=False)
        context += markdown_string
    except Exception as e:
        st.error(f"Error converting DataFrame to Markdown: {e}")
        context += "[Error converting DataFrame to Markdown]"
    context += "\n```\n" # to properly terminate the markdown code block
    return context


# --- Streamlit App UI ---

st.set_page_config(layout="wide")
st.title("AI Powered Data Explorer")

# --- File Upload Section ---
with st.sidebar:
    st.header("1. Upload Files")
    uploaded_files = st.file_uploader(
        "Upload CSV or XLSX files!",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        help="Upload one or more data files. Note that only CSV or XLSX files are accepted.",
    )

    if uploaded_files:
        new_files_uploaded = False
        current_filenames = set(st.session_state.uploaded_files_info.keys())
        uploaded_filenames = set(f.name for f in uploaded_files)

        if current_filenames != uploaded_filenames: # New file uploaded
            new_files_uploaded = True
            st.session_state.uploaded_files_info = {
                f.name: {"content": f.getvalue(), "type": f.type}
                for f in uploaded_files
            }
            st.session_state.dataframes = {}
            st.session_state.messages = []
            st.info("New files detected. Reloading dataframes...")

        temp_dfs = {}
        for filename, file_info in st.session_state.uploaded_files_info.items():
            loaded_dfs = load_dataframe(file_info, filename)
            temp_dfs.update(loaded_dfs)

        if st.session_state.dataframes.keys() != temp_dfs.keys():
            st.session_state.dataframes = temp_dfs
            st.rerun()

    if st.session_state.dataframes:
        st.subheader("Loaded DataFrames/Sheets:")
        df_keys = list(st.session_state.dataframes.keys())
        st.write(df_keys)
    else:
        st.info("Upload files to get started.")


# --- Main Area ---
col1, col2 = st.columns(2)

# --- Data Display Section ---
with col1:
    st.header("2. View Data")
    if st.session_state.dataframes:
        df_keys = list(st.session_state.dataframes.keys())
        selected_key_view = st.selectbox(
            "Select DataFrame/Sheet to view:", df_keys, key="view_select"
        )

        if selected_key_view:
            selected_df_view = st.session_state.dataframes[selected_key_view]
            st.subheader(f"Top N rows of: {selected_key_view}")
            num_rows = st.number_input(
                "Number of rows to display:",
                min_value=1,
                max_value=len(selected_df_view),
                value=min(5, len(selected_df_view)),
                key="num_rows_view",
            )
            st.dataframe(selected_df_view.head(num_rows))
    else:
        st.info("Upload files and load data to view.")

# --- Chat Section ---
with col2:
    st.header("3. Ask Questions (AI)")

    if st.session_state.dataframes:
        df_keys_chat = list(st.session_state.dataframes.keys())

        selected_key_chat = st.selectbox(
            "Select DataFrame/Sheet for AI context:",
            df_keys_chat,
            key="chat_select",
            index=df_keys_chat.index(st.session_state.selected_df_key_for_chat)
            if st.session_state.selected_df_key_for_chat in df_keys_chat
            else 0,
        )
        if selected_key_chat != st.session_state.selected_df_key_for_chat:
            st.session_state.selected_df_key_for_chat = selected_key_chat

        st.subheader(f"Chat about: {st.session_state.selected_df_key_for_chat}")

        # Display chat messages
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    feedback_key_base = f"feedback_{i}"
                    (
                        col_feedback1,
                        col_feedback2,
                        col_feedback_rest,
                    ) = st.columns([1, 1, 5])
                    with col_feedback1:
                        if st.button(
                            "👍", key=f"{feedback_key_base}_up", help="Useful"
                        ):
                            st.toast(
                                f"Feedback received for message {i}: Useful",
                                icon="👍",
                            )
                    with col_feedback2:
                        if st.button(
                            "👎",
                            key=f"{feedback_key_base}_down",
                            help="Not Useful",
                        ):
                            st.toast(
                                f"Feedback received for message {i}: Not Useful",
                                icon="👎",
                            )

        # Accept user input
        if prompt := st.chat_input(
            f"Ask a question about {st.session_state.selected_df_key_for_chat}..."
        ):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Prepare context and call AI
            try:
                selected_df_chat = st.session_state.dataframes[
                    st.session_state.selected_df_key_for_chat
                ]

                # --- Generate full DataFrame context ---
                with st.spinner("Converting DataFrame to Markdown for context..."):
                    data_context = get_dataframe_context(
                        selected_df_chat, st.session_state.selected_df_key_for_chat
                    )
            
                system_prompt = (
                    "You are a helpful data analysis assistant. "
                    "You have been provided with the entire content of a DataFrame in Markdown format. "
                    "Answer the user's question based only on the provided DataFrame content. "
                    "Perform calculations or analysis as requested if possible based on the full data.\n"
                    "--- DataFrame Content ---\n"
                    f"{data_context}\n"
                    "--- End DataFrame Content ---"
                )

                messages_for_api = [
                    {"role": "system", "content": system_prompt},
                    # History might need to be excluded if context is huge
                    {"role": "user", "content": prompt}
                ]

                # Display thinking indicator
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        start_time = time.time()
                        response = client.chat.completions.create(
                            model="gpt-4-turbo", 
                            messages=messages_for_api,
                            temperature=0.2,
                        )
                        ai_response = response.choices[0].message.content
                        end_time = time.time()
                        st.markdown(ai_response)
                        st.caption(f"Response generated in {end_time - start_time:.2f} seconds")


                st.session_state.messages.append(
                    {"role": "assistant", "content": ai_response}
                )

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Sorry, an error occurred: {e}"}
                )

    else:
        st.info("Upload files to enable the chat feature.")
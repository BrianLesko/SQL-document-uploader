# Brian Lesko
# 11/24/2023

import streamlit as st
from SQLConnect import SQLConnectDocker as SQLConnect
from customize_gui import gui as gui 
gui = gui()
import lz4.frame
import Quartz # pip install pyobjc
from CoreFoundation import CFURLCreateFromFileSystemRepresentation
import os

def extract_text_from_pdf(pdf_path):
    pdf_url = CFURLCreateFromFileSystemRepresentation(
        None, pdf_path.encode('utf-8'), len(pdf_path), False
    )
    pdf_doc = Quartz.PDFKit.PDFDocument.alloc().initWithURL_(pdf_url)

    if pdf_doc is None:
        print(f"Failed to load PDF file: {pdf_path}")
        return None

    extracted_text = ""
    for i in range(pdf_doc.pageCount()):
        page = pdf_doc.pageAtIndex_(i)
        if page is not None:
            page_text = page.string()
            if page_text is not None:
                extracted_text += page_text

    return extracted_text

def compress(text_data):
    compressed_data = lz4.frame.compress(text_data.encode())
    return compressed_data

def decompress(compressed_data):
    decompressed_data = lz4.frame.decompress(compressed_data)
    return decompressed_data

def main(): 

    gui.setup(wide=True, text="Extract Text from PDF files. Enter the path to the file.")
    st.title('Extract Text from PDF files')
    current_task = st.empty()

    if "sql" not in st.session_state:
        st.session_state.sql = SQLConnect()
        st.session_state.sql.connect()
    if "sql" in st.session_state:
        sql = st.session_state.sql

    with st.sidebar:
        result = sql.get_summary()
        Databases = st.empty()
        with Databases: st.table(result)
        "---"
        st.write('Docker installed:', sql.docker_version)
        st.write('Docker running:', sql.docker_is_running)
        if not sql.docker_is_running: 
            st.write("Docker is not running")
        st.write('Container running:', sql.container_is_running)

        if st.button("Restart the MySQL Container"):
            sql.stop_container()
            sql.start_container()

        # List all PDF files in the directory without extensions
        directory = "documents/"
        files = [os.path.splitext(f)[0] for f in os.listdir(directory) if f.endswith('.pdf')]
        # write the names of the files to the sidebar
        "---"
        st.header("Files in the directory:")
        for file in files:
            st.write(file)
    
    sql.query("USE user")
    existing = sql.query("SELECT name FROM size;")
    st.write(f"{len(existing)} Rows in the database.")
    # Convert existing to a set
    existing_files = set([file['name'] for file in existing])
    st.write(f"{len(existing_files)} Unique files in the database.")
    # Convert files to a set and get the difference
    to_upload = list(set(files) - existing_files)
    st.write(f"{len(to_upload)} files to upload.")

    directory_structure = sql.describe_table("size")
    for column in directory_structure:
        print(column)

    for file in to_upload:
        path = directory + file + '.pdf'

        with st.spinner('Extracting text from PDF...'):
            text = extract_text_from_pdf(path)
        if text:
            with st.spinner('Encoding the text as UTF-8...'):
                encoded_text = text.encode()
            with st.spinner('Compressing the text...'):
                compressed_text = compress(text)
            name = str(file)
            length = len(text)
            encoded_length = len(encoded_text)
            compressed_length = len(compressed_text)

            # write to the SQL database in a new table called directory where the columns are name, length, encoded_length, and compressed_length
            current_task.write(f"Writing {path} to the SQL database...")
            sql.write_to_table(name, length, encoded_length, compressed_length)
            sql.cursor.execute("INSERT INTO content (name, content) VALUES (%s, %s);", (name, text))
main()
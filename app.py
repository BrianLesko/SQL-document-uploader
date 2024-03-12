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
            extracted_text += page.string()

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

        # List all files in the directory
        directory = "documents/"
        files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]

        # write the names of the files to the sidebar
        st.write("Files in the directory:")
        for file in files:
            st.write(file)

    path = st.text_input("Enter the path to the PDF file:")
    
    if path: 
        st.write(f"Path: {path}")
        with st.spinner('Extracting text from PDF...'):
            text = extract_text_from_pdf(path)
        if text:
            st.write(f"There are {len(text)} characters in the PDF file.")
            with st.spinner('Encoding the text as UTF-8...'):
                encoded_text = text.encode()
            st.write(f"Encoding the text as UTF-8, the file is {len(encoded_text)} bytes.")
            with st.spinner('Compressing the text...'):
                compressed_text = compress(text)
            st.write(f"When compressed, the file is {len(compressed_text)} bytes.")
            # print the compression ratio
            st.write(f"The compression ratio is {len(compressed_text)/len(encoded_text):.2f}.")
            # decompress the text
            with st.spinner('Decompressing the text...'):
                decompressed_text = decompress(compressed_text)
            st.write(f"The decompressed, encoded text is {len(decompressed_text)} characters.")
            # decode the text
            with st.spinner('Decoding the text...'):
                decoded_text = decompressed_text.decode()
            st.write(f"The decoded text is {len(decoded_text)} characters.")

main()
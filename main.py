from pathlib import Path
import streamlit as st

import sections
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# 记录到文件

logging.basicConfig(level=logging.INFO, filename='log.log')

# Main content based on the selected page
root_index_path = Path("all_index")

if "title" not in st.session_state:
    st.session_state.title = "Index Stage"

st.title(st.session_state.title)

if not st.session_state.get('choose'):
    st.markdown("## Choose an Option")
    # Provide options to Load Historical Index or Create New Index side by side
    col1, col2 = st.columns(2)

    # Buttons to set session state
    with col1:
        st.button("Load Historical Index", use_container_width=True, on_click=sections.set_state, kwargs={'load_historic': True, 'create_new': False})

    with col2:
        st.button("Create New Index", use_container_width=True, on_click=sections.set_state, kwargs={'load_historic': False, 'create_new': True})

    st.session_state.choose = True

if st.session_state.get('load_historic'):
    sections.load_history_index(root_index_path)

if st.session_state.get('create_new'):
    sections.create_new_index(root_index_path)

import asyncio
import multiprocessing
import time

import yaml
from graphrag.prompt_tune.cli import prompt_tune
from httpx import ReadTimeout
from openai import OpenAI

import utils
import streamlit as st
from graphrag.index.cli import index_cli, _get_progress_reporter, _initialize_project_at


def show_index_config(index_path):
    config_file = index_path / 'settings.yaml'
    env_file = index_path / '.env'
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            llm_model = config['llm']['model']
    if env_file.exists():
        with open(env_file, 'r') as f:
            env = f.readlines()
            for _ in env:
                split_data = _.split('=')
                if split_data[0] == 'GRAPHRAG_API_KEY':
                    llm_api_key = split_data[1]
                if split_data[0] == 'GRAPHRAG_API_BASE':
                    llm_base_url = split_data[1]

    co_1, co_2 = st.columns(2)
    with co_1:
        new_llm_base_url = st.text_input("LLM Base URL", placeholder=llm_base_url, key='llm_base_url', value=llm_base_url)
    with co_2:
        new_llm_api_key = st.text_input("LLM API Key", placeholder=llm_api_key, key='llm_api_key', value=llm_api_key)
    new_llm_model = st.text_input("LLM Model", placeholder="Enter the LLM model", key='llm_model', value=llm_model)
    if new_llm_api_key != llm_api_key or new_llm_base_url != llm_base_url or new_llm_model != llm_model:
        st.button("Update", on_click=set_state, kwargs={'load_stage': -2})
    else:
        st.button("Submit", on_click=set_state, kwargs={'load_stage': -1})


def show_chat(index_dir_path, server_url="http://localhost:20213/v1"):
    openai_base_url = server_url
    # Set OpenAI API key from Streamlit secrets
    client = OpenAI(base_url=openai_base_url, api_key=None)

    # choose which output dir
    all_output_dirs = utils.get_folders_sorted_by_creation_time(index_dir_path / 'output')
    print(all_output_dirs)
    st.session_state['output_dir'] = [_.name for _ in all_output_dirs.values()][0]

    # choose method
    methods = ['local', 'global']
    method = st.selectbox("Select Method", methods)
    st.session_state['method'] = method

    # Set a default model
    # if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = f"{st.session_state['output_dir']}-{method}"

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if message["role"] == "assistant":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Here input your question"):
        print(st.session_state.messages)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})


def load_history_index(root_index_path):
    st.session_state['load_header'] = "Load Historical Index" if 'load_header' not in st.session_state else st.session_state.get('load_header')
    st.markdown(f"### {st.session_state.get('load_header')}")
    # Implement loading logic here, e.g., list available historical indexes
    if 'load_stage' not in st.session_state:
        st.session_state.load_stage = 0
    if st.session_state.load_stage == 0:
        show_available_indexes = utils.get_folders_sorted_by_creation_time(root_index_path)  # This should be dynamically loaded
        selected_index = st.selectbox("Select Historical Index", show_available_indexes.keys())
        st.button("Load Index", on_click=set_state,
                  kwargs={'load_stage': 1, 'index_dir_path': show_available_indexes[selected_index], 'show_index_name': selected_index})
    if st.session_state.load_stage == 1:
        st.session_state['load_header'] = f"Index Name: `{st.session_state.show_index_name}`"
        st.session_state.load_stage = 2
        st.rerun()
    if st.session_state.load_stage >= 2:
        # show index details
        show_index_config(st.session_state.index_dir_path)
    if st.session_state.load_stage == -2:
        # update config
        with st.spinner('Configuring indexing...'):
            env_file = st.session_state.index_dir_path / '.env'
            with open(env_file, 'w') as f:
                f.write(f"GRAPHRAG_API_BASE={st.session_state.llm_base_url}\n")
                f.write(f"GRAPHRAG_API_KEY={st.session_state.llm_api_key}\n")
                f.write(f"GRAPHRAG_EMBEDDING_API_BASE={st.session_state.llm_base_url}\n")
            setting_file = st.session_state.index_dir_path / 'settings.yaml'

            with open(setting_file, 'r') as f:
                config = yaml.safe_load(f)
                config['llm']['model'] = st.session_state.llm_model
            with open(setting_file, 'w') as f:
                yaml.dump(config, f)
        st.success("Update Config Completed")
        st.session_state.load_stage = -1
        st.rerun()
    if st.session_state.load_stage == -1:
        # load chat ui
        with st.spinner('Starting WebServer...'):
            utils.start_webserver(st.session_state.index_dir_path)
        st.success("WebServer Started")
        # jump to query
        st.button("Complete! Start Chat", use_container_width=True, on_click=set_state, kwargs={**st.session_state, 'load_stage': -3})
    if st.session_state.load_stage == -3:
        st.session_state.title = "Chat Stage"
        show_chat(st.session_state.index_dir_path)


def create_new_index(root_index_path):
    st.session_state['new_index_header'] = "Create New Index" if 'new_index_header' not in st.session_state else st.session_state.get('new_index_header')
    st.markdown(f"#### {st.session_state.get('new_index_header')}")
    if 'create_stage' not in st.session_state:
        st.session_state.create_stage = 0
    if st.session_state.create_stage == 0:
        index_name = st.text_input("Enter Index Name")
        st.button("Create Index", on_click=set_state, kwargs={'create_stage': 1, 'index_name': index_name})
    if st.session_state.create_stage == 1:
        is_create, index_dir_path = utils.create_folder(root_index_path, st.session_state.index_name)
        if is_create:
            st.session_state['new_index'] = True
        else:
            st.session_state['new_index'] = False

        st.session_state['index_dir_path'] = index_dir_path

        st.session_state['new_index_header'] = f"Index Name: `{st.session_state.index_name}`"

        st.session_state.create_stage = 2
        st.rerun()

    if st.session_state.create_stage >= 2:
        if st.session_state.get('new_index'):
            set_config()  # create config
        else:
            st.warning(f"Index `{st.session_state.get('index_name')}` already exists.")

    if st.session_state.create_stage >= 3:
        print(st.session_state)
        st.markdown("### <span style='color:red; font-weight:bold;'>Please enter `yes` to start indexing</span>", unsafe_allow_html=True)
        st.text_input('', key='confirm_index')
        if st.session_state.confirm_index == 'yes':
            st.button("Start Indexing", on_click=set_state, kwargs={'create_stage': -1}, disabled=False)
        if st.session_state.confirm_index != 'yes':
            st.button("Start Indexing", on_click=set_state, kwargs={'create_stage': -1}, disabled=True)

    if st.session_state.create_stage == -1:
        print(st.session_state)
        domain = st.session_state.domain
        language = st.session_state.language
        index_dir_path = str(st.session_state.index_dir_path.absolute())
        st.markdown("### Indexing Started")

        # init index dir
        with st.spinner('Wait for init index directory...'):
            reporter = _get_progress_reporter('none')
            _initialize_project_at(index_dir_path, reporter)
        st.success("Indexing Init Completed")
        # config
        with st.spinner('Configuring indexing...'):
            env_file = st.session_state.index_dir_path / '.env'
            with open(env_file, 'w') as f:
                f.write(f"GRAPHRAG_API_BASE={st.session_state.llm_base_url}\n")
                f.write(f"GRAPHRAG_API_KEY={st.session_state.llm_api_key}\n")
                f.write(f"GRAPHRAG_EMBEDDING_API_BASE={st.session_state.llm_base_url}\n")
            setting_file = st.session_state.index_dir_path / 'settings.yaml'

            with open(setting_file, 'r') as f:
                config = yaml.safe_load(f)
                config['input']['file_type'] = 'text' if st.session_state.file_type == 'txt' else 'csv'
                config['input']['file_pattern'] = f".*\\.{st.session_state.file_type}$"
                config['llm']['model'] = st.session_state.llm_model
            with open(setting_file, 'w') as f:
                yaml.dump(config, f)

        st.success("Indexing Configuration Completed")

        # prompt tuning
        if domain or language:
            with st.spinner('Prompt Tuning...'):
                process = multiprocessing.Process(target=prompt_tuning, args=(index_dir_path, domain, language))
                process.start()
                process.join()

            st.success("Prompt Tuning Completed")

        # begin indexing
        with st.spinner('Indexing...'):
            process = multiprocessing.Process(target=begin_indexing, args=(index_dir_path,))
            process.start()
            process.join()
        st.success("Indexing Completed")

        # jump to load index
        st.button("Complete! Jump to load Index", use_container_width=True, on_click=set_state,
                  kwargs={'load_historic': True, 'create_new': False, 'create_stage': 0})


def set_config():
    st.markdown("### Set Configuration and Data")
    with st.form(key='config_form'):
        # Inputs for configuration
        co_1, co_2 = st.columns(2)
        with co_1:
            llm_base_url = st.text_input("LLM Base URL", placeholder="Enter the URL for LLM base", value='https://aihubmix.com/v1')
            domain = st.text_input("Domain", placeholder="Enter the domain")
        with co_2:
            llm_api_key = st.text_input("LLM API Key", placeholder="Enter your API key for LLM")
            language = st.text_input("Language", placeholder="Enter the language")

        llm_model = st.text_input("LLM Model", placeholder="Enter the LLM model", value='gpt-4o-mini')

        file_type = st.selectbox('Choose Data File Type', ['csv', 'txt'])

        uploaded_file = st.file_uploader("Choose CSV file", type=['csv', 'txt'], accept_multiple_files=True)

        if uploaded_file is not None:
            input_dir_path = st.session_state.index_dir_path / 'input'
            if not input_dir_path.exists():
                input_dir_path.mkdir(parents=True)

            for file in uploaded_file:
                with open(input_dir_path / file.name, 'wb') as f:
                    f.write(file.getbuffer())
        if st.form_submit_button(label='Submit', on_click=set_state, kwargs={**st.session_state, 'create_stage': 3}):
            st.session_state.file_type = file_type
            st.session_state.llm_base_url = llm_base_url
            st.session_state.llm_api_key = llm_api_key
            st.session_state.domain = domain
            st.session_state.language = language
            st.session_state.llm_model = llm_model

            st.success("Configuration and Data set successfully.")


def set_state(**kwargs):
    for key, value in kwargs.items():
        st.session_state[key] = value


def prompt_tuning(root_dir, domain, language):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        prompt_tune(
            root_dir,
            domain,
            'all',
            15,
            2000,
            200,
            language,
            False,
            'prompts',
            300,
            15,
            2,
        )
    )


def begin_indexing(root_dir):
    index_cli(
        root=root_dir,
        verbose=False,
        resume=None,
        memprofile=False,
        nocache=False,
        reporter='none',
        config=None,
        emit='parquet,csv',
        dryrun=False,
        init=False,
        overlay_defaults=False,
        cli=True,
    )

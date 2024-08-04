import os
from pathlib import Path

import yaml
from azure.identity import get_bearer_token_provider, DefaultAzureCredential
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from graphrag.config import LLMParameters, TextEmbeddingConfig, LocalSearchConfig, GlobalSearchConfig, LLMType
from graphrag.query.llm.oai import OpenaiApiType


class Settings(BaseSettings):
    server_host: str = "http://localhost"
    server_port: int = 20213
    data: str = (
        "./output"
    )
    lancedb_uri: str = (
        "./lancedb"
    )
    llm: LLMParameters
    embeddings: TextEmbeddingConfig
    global_search: GlobalSearchConfig
    local_search: LocalSearchConfig
    encoding_model: str = "cl100k_base"

    def is_azure_client(self):
        return self.llm.type == LLMType.AzureOpenAIChat or settings.llm.type == LLMType.AzureOpenAI

    def get_api_type(self):
        return OpenaiApiType.AzureOpenAI if self.is_azure_client() else OpenaiApiType.OpenAI

    def azure_ad_token_provider(self):
        if self.llm.cognitive_services_endpoint is None:
            cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
        else:
            cognitive_services_endpoint = settings.llm.cognitive_services_endpoint
        if self.is_azure_client() and not settings.llm.api_key:
            return get_bearer_token_provider(DefaultAzureCredential(), cognitive_services_endpoint)
        else:
            return None


def load_settings_from_index_dir(index_dir_path: str) -> Settings:
    file_path = Path(index_dir_path) / 'settings.yaml'
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    llm_config = config['llm']
    embeddings_config = config['embeddings']
    global_search_config = config['global_search'] or {}
    local_search_config = config['local_search'] or {}
    encoding_model = config['encoding_model']

    # Manually setting the API keys from environment variables if specified
    load_dotenv(Path(index_dir_path) / '.env')

    llm_params = LLMParameters(**llm_config)
    llm_params.api_key = os.environ.get("GRAPHRAG_API_KEY", llm_config['api_key'])
    llm_params.api_base = os.environ.get("GRAPHRAG_API_BASE")
    text_embedding = TextEmbeddingConfig(**embeddings_config)
    text_embedding.llm.api_key = os.environ.get("GRAPHRAG_API_KEY", embeddings_config['llm']['api_key'])
    text_embedding.llm.api_base = os.environ.get("GRAPHRAG_EMBEDDING_API_BASE")

    print(text_embedding)
    setting = Settings(
        data=str(Path(index_dir_path) / 'output'),
        llm=llm_params,
        embeddings=text_embedding,
        global_search=GlobalSearchConfig(**global_search_config),
        local_search=LocalSearchConfig(**local_search_config),
        encoding_model=encoding_model
    )

    return setting


with open('webserver/configs/index_dir', 'r') as f:
    index_dir = f.read().strip()
    settings = load_settings_from_index_dir(index_dir)
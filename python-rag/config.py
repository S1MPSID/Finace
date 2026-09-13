from pathlib import Path
from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "compliance_engine"

    # LLM — Gemini 2.5 Flash (primary)
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="GEMINI_BASE_URL",
    )

    # Optional fallbacks
    nvidia_api_key: str = Field(default="", alias="NVIDIA_API_KEY")
    nvidia_model: str = Field(
        default="nvidia/nemotron-3.5-lightning-30b-a3b",
        alias="NVIDIA_MODEL",
    )
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        alias="NVIDIA_BASE_URL",
    )
    llm_max_tokens: int = Field(default=8192, alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_top_p: float = Field(default=0.9, alias="LLM_TOP_P")
    llm_reasoning_budget: int = Field(default=0, alias="LLM_REASONING_BUDGET")

    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    xai_model: str = Field(default="grok-3-mini", alias="XAI_MODEL")
    xai_base_url: str = Field(default="https://api.x.ai/v1", alias="XAI_BASE_URL")

    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_dim: int = 1024
    embedding_backend: str = Field(default="fastembed", alias="EMBEDDING_BACKEND")
    rag_light_xai: bool = Field(default=False, alias="RAG_LIGHT_XAI")
    retrieval_max_candidates: int = Field(default=300, alias="RETRIEVAL_MAX_CANDIDATES")

    # IPFS / Pinata
    pinata_api_key: str = ""
    pinata_secret_key: str = ""
    pinata_jwt: str = ""

    # Blockchain
    blockchain_rpc_url: str = "http://127.0.0.1:8545"
    compliance_contract_address: str = ""

    # Paths (resolved relative to this file; DATA_DIR / RBI_DOCS_DIR override via .env)
    project_root: Path = Path(__file__).resolve().parent.parent
    service_root: Path = Path(__file__).resolve().parent
    data_dir: Path = Field(default=Path("../data"), alias="DATA_DIR")
    rbi_docs_dir: Path = Field(default=Path("../RBI DOCS"), alias="RBI_DOCS_DIR")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def normalize_project_paths(self):
        project_root = Path(__file__).resolve().parent.parent
        service_root = Path(__file__).resolve().parent
        self.project_root = project_root
        self.service_root = service_root

        data_dir = Path(self.data_dir)
        if not data_dir.is_absolute():
            data_dir = (service_root / data_dir).resolve()
        self.data_dir = data_dir

        rbi_docs_dir = Path(self.rbi_docs_dir)
        if not rbi_docs_dir.is_absolute():
            rbi_docs_dir = (service_root / rbi_docs_dir).resolve()
        self.rbi_docs_dir = rbi_docs_dir
        return self


settings = Settings()

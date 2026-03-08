import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    openai_api_key: str
    openai_model_chat: str
    openai_model_embed: str
    line_channel_secret: str
    line_channel_access_token: str
    pg_host: str
    pg_port: int
    pg_db: str
    pg_user: str
    pg_password: str
    spreadsheet_url: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            openai_model_chat=os.getenv("OPENAI_MODEL_CHAT", "gpt-4o-mini"),
            openai_model_embed=os.getenv("OPENAI_MODEL_EMBED", "text-embedding-3-small"),
            line_channel_secret=os.environ["LINE_CHANNEL_SECRET"],
            line_channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
            pg_host=os.environ["PG_HOST"],
            pg_port=int(os.getenv("PG_PORT", "5432")),
            pg_db=os.environ["PG_DB"],
            pg_user=os.environ["PG_USER"],
            pg_password=os.environ["PG_PASSWORD"],
            spreadsheet_url=os.getenv("SPREADSHEETURL", ""),
        )


settings = Config.from_env()

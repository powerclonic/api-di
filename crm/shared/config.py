from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://crm:crm@localhost:5432/crm"

    api_url: str
    api_organization: str = "0000"  # query `organization` do Core
    api_key: str
    api_secret: str

    # Entra ID
    auth_url: str
    auth_tenant: str
    auth_client_id: str
    auth_client_secret: str
    auth_redirect_uri: str = "http://localhost:8000/auth/callback"
    auth_scope: str = "openid profile email offline_access"

    # BFF / sessão
    frontend_url: str = "http://localhost:8000/auth/me"
    session_secret: str  # assina o cookie temporário do login (state/nonce/PKCE)
    session_cookie_name: str = "crm_session"
    session_cookie_secure: bool = False  # True fora do dev (HTTPS)
    session_ttl_segundos: int = 8 * 3600  # vida máxima absoluta da sessão

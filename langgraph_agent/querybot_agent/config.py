"""
Agent configuration, resolved from the environment.
"""
import os
from dataclasses import dataclass, field


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, ''))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, ''))
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() not in ('false', '0', 'no', 'off')


# Provider catalogues change faster than this file, so set LLM_MODEL explicitly
# if the default model has been retired or renamed.
DEFAULT_GEMINI_MODEL = 'gemini-2.5-pro'


def _resolve_sqlite_url() -> str:
    url = os.environ.get('SQLITE_SERVICE_URL', 'http://localhost:3001').rstrip('/')
    if ('localhost:3001' in url or '127.0.0.1:3001' in url) and (
        os.path.exists('/.dockerenv') or os.environ.get('IN_DOCKER')
    ):
        return 'http://sqlite-service:3001'
    return url


@dataclass(frozen=True)
class Settings:
    """Runtime settings resolved from the environment."""

    # Dataset service
    sqlite_service_url: str = field(default_factory=_resolve_sqlite_url)
    service_token: str = field(default_factory=lambda: os.environ.get('SERVICE_TOKEN', ''))
    request_timeout: int = field(default_factory=lambda: _int_env('SQLITE_REQUEST_TIMEOUT', 60))

    # Google Gemini is the only supported model provider.
    llm_model: str = field(default_factory=lambda: os.environ.get('LLM_MODEL', '').strip())

    temperature: float = field(default_factory=lambda: _float_env('TEMPERATURE', 0.0))
    max_retries: int = field(default_factory=lambda: _int_env('LLM_MAX_RETRIES', 2))
    max_output_tokens: int = field(default_factory=lambda: _int_env('LLM_MAX_OUTPUT_TOKENS', 4096))

    # Chart generation
    charts_dir: str = field(default_factory=lambda: os.environ.get('CHART_OUTPUT_DIR', 'generated_charts'))
    chart_timeout: int = field(default_factory=lambda: _int_env('CHART_TIMEOUT', 120))
    chart_image_name: str = field(
        default_factory=lambda: os.environ.get('CHART_EXECUTOR_IMAGE', 'querybot-chart-executor')
    )
    # Docker isolates chart code from the host. Disabling it runs generated code
    # in-process and is intended only for environments without a Docker daemon.
    chart_docker_enabled: bool = field(
        default_factory=lambda: os.environ.get('CHART_DOCKER_ENABLED', 'true').lower() != 'false'
    )

    # Query limits
    max_result_rows: int = field(default_factory=lambda: _int_env('MAX_RESULT_ROWS', 5000))
    # Rows sent to the model for analysis; the full set still reaches the client.
    llm_sample_rows: int = field(default_factory=lambda: _int_env('LLM_SAMPLE_ROWS', 30))

    # How many times a failing query is rewritten using the database's error
    # message as feedback. Two repairs recovers most fixable failures; beyond that
    # the model tends to loop on the same mistake, so it is not worth the latency.
    max_sql_repairs: int = field(default_factory=lambda: _int_env('MAX_SQL_REPAIRS', 2))

    # Follow-up question suggestions after each answer.
    suggest_followups: bool = field(
        default_factory=lambda: os.environ.get('SUGGEST_FOLLOWUPS', 'true').lower() != 'false'
    )

    # Conversational refinement: recognise a follow-up that only changes how the
    # previous answer is presented ("make it a pie chart") and rewrite that result
    # instead of running the whole workflow again. Disable to always re-query.
    refine_followups: bool = field(default_factory=lambda: _bool_env('REFINE_FOLLOWUPS', True))

    @property
    def model(self) -> str:
        """The Gemini model to call."""
        return self.llm_model or DEFAULT_GEMINI_MODEL

    @property
    def auth_headers(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.service_token}'} if self.service_token else {}


settings = Settings()

"""Gemini model access and tolerant response parsing."""
import json
import logging
import os
import re
import threading
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from querybot_agent.config import settings

logger = logging.getLogger(__name__)


class LLMConfigurationError(RuntimeError):
    """Raised when the selected provider cannot be used as configured."""


def _build_client() -> BaseChatModel:
    """Construct the configured Google Gemini chat client."""
    model = settings.model
    if not model:
        raise LLMConfigurationError('No Gemini model is configured. Set LLM_MODEL.')

    if not os.environ.get('GOOGLE_API_KEY'):
        raise LLMConfigurationError('Google Gemini requires GOOGLE_API_KEY to be set.')

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise LLMConfigurationError('Google Gemini requires the langchain-google-genai package.') from exc

    logger.info('Using Google Gemini model %s', model)
    return ChatGoogleGenerativeAI(
        model=model,
        max_retries=settings.max_retries,
        max_output_tokens=settings.max_output_tokens,
        temperature=settings.temperature,
    )


class LLMManager:
    """Single entry point for model calls."""

    # The client is stateless and thread-safe; one instance is shared across the
    # many manager objects the workflow creates, instead of opening a new client
    # per node on every run.
    _shared_client: Optional[BaseChatModel] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.llm = self._client()

    @classmethod
    def _client(cls) -> BaseChatModel:
        if cls._shared_client is None:
            with cls._lock:
                if cls._shared_client is None:
                    cls._shared_client = _build_client()
        return cls._shared_client

    @classmethod
    def reset(cls) -> None:
        """Drop the cached client so the next call re-reads the configuration."""
        with cls._lock:
            cls._shared_client = None

    def invoke(self, prompt: ChatPromptTemplate, **kwargs: Any) -> str:
        """Render the prompt, call the model, and return the text response."""
        messages = prompt.format_messages(**kwargs)
        response = self.llm.invoke(messages)

        return _text_of(response.content)

    def invoke_json(self, prompt: ChatPromptTemplate, **kwargs: Any) -> Any:
        """
        Call the model and parse the response as JSON.

        Models routinely wrap JSON in a ```json fence or add a sentence of
        commentary. Rather than letting the strict parser fail the whole run, the
        outermost JSON object is extracted as a fallback.
        """
        raw = self.invoke(prompt, **kwargs)

        try:
            return JsonOutputParser().parse(raw)
        except Exception:  # noqa: BLE001 - fall through to lenient extraction
            logger.debug('Strict JSON parse failed, attempting extraction')

        cleaned = re.sub(r'^\s*```(?:json)?|```\s*$', '', raw.strip(), flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f'The model did not return valid JSON: {raw[:200]}')


def _text_of(content: Any) -> str:
    """
    Flatten a response body to text.

    Gemini may return a plain string or a list of content blocks. Blocks without
    text must be dropped rather than stringified into JSON responses.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get('type') in ('thinking', 'redacted_thinking'):
                    continue
                parts.append(str(block.get('text', '')))
            else:
                parts.append(str(block))
        return ''.join(parts)

    return str(content)

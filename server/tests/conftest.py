import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.config import settings
from app.database import configure_engine
from app.extensions import db as _db
from app.models.dataset_model import Dataset
from app.models.user_model import User


class TestClientWrapper(TestClient):
    def open(self, path: str, method: str = 'GET', **kwargs):
        return self.request(method, path, **kwargs)

    def request(self, method: str, url: str, **kwargs):
        response = super().request(method, url, **kwargs)
        if not hasattr(response, 'get_json'):
            response.get_json = response.json
        if not hasattr(response, 'get_data'):
            response.get_data = lambda as_text=False: response.text if as_text else response.content
        if not hasattr(response, 'data'):
            response.data = response.content
        return response


@pytest.fixture(autouse=True)
def reset_rate_limits():
    from app.utils.rate_limit import limiter
    limiter.reset()


@pytest.fixture()
def app():
    settings.DATABASE_URL = 'sqlite:///:memory:'
    configure_engine(settings.DATABASE_URL)
    application = create_app('testing')

    _db.create_all()
    yield application
    _db.session.remove()
    _db.drop_all()


@pytest.fixture()
def client(app):
    return TestClientWrapper(app)


@pytest.fixture()
def db(app):
    return _db


def _create_user(email: str) -> User:
    user = User(
        fullname='Test User',
        email=email,
        password_hash='disabled-test-account',
    )
    user.save()
    return user


@pytest.fixture()
def user(app):
    return _create_user('owner@example.com')


@pytest.fixture()
def other_user(app):
    return _create_user('stranger@example.com')


@pytest.fixture()
def dataset(app, user):
    import uuid as uuid_module

    record = Dataset(
        external_uuid=uuid_module.uuid4(),
        user_id=user.id,
        file_name='sales.csv',
        size_bytes=1024,
        table_count=1,
        row_count=100,
    )
    record.save()
    return record


@pytest.fixture()
def stub_agent(monkeypatch):
    from app.services import langgraph_service

    calls: list[dict] = []

    def _fake_stream(question, dataset_uuid, history=None, previous=None):
        calls.append(
            {
                'question': question,
                'dataset_uuid': dataset_uuid,
                'history': history,
                'previous': previous,
            }
        )
        result = {'answer': f'Stubbed answer for: {question}'}
        yield 'data: {"format_results": {"answer": "Stubbed answer"}}\n\n', result

    _fake_stream.calls = calls  # type: ignore[attr-defined]
    monkeypatch.setattr(langgraph_service, 'stream_run', _fake_stream)
    return _fake_stream


@pytest.fixture()
def sign_in(client):
    def _sign_in(email: str) -> None:
        return None

    return _sign_in

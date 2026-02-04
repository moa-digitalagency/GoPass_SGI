import pytest
import os
from app import create_app
from models import db, TelegramSubscriber, TelegramBotConfig
from services import TelegramService
import json

# Ensure env vars are set for testing
os.environ['SESSION_SECRET'] = 'test_secret'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:' # Use in-memory DB for tests
os.environ['TELEGRAM_ENCRYPTION_KEY'] = 'UhdQvTy_azauEg2rN6adlJV9gGyx6xPGXWU06Lqsh5M='

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_encryption(app):
    with app.app_context():
        token = "12345:ABCDEF"
        enc = TelegramService.encrypt_token(token)
        assert enc != token
        dec = TelegramService.decrypt_token(enc)
        assert dec == token

def test_register_subscriber(app):
    with app.app_context():
        sub, created = TelegramService.register_subscriber('123', 'testuser', 'Test')
        assert created
        assert sub.chat_id == '123'
        assert sub.status == 'PENDING'

        sub2, created2 = TelegramService.register_subscriber('123', 'testuser', 'Test')
        assert not created2

def test_webhook(client, app):
    update = {
        "update_id": 10000,
        "message": {
            "message_id": 1365,
            "from": {
                "id": 1111111,
                "is_bot": False,
                "first_name": "John",
                "username": "johndoe",
                "language_code": "en"
            },
            "chat": {
                "id": 1111111,
                "first_name": "John",
                "username": "johndoe",
                "type": "private"
            },
            "date": 1441645532,
            "text": "/start"
        }
    }

    # Mock send_message_sync to avoid real API calls or errors
    # We can just let it fail/log error, as the webhook endpoint catches exceptions or ignores failures
    # But to be clean we should verify the DB side effect.

    res = client.post('/api/telegram/webhook', data=json.dumps(update), content_type='application/json')
    assert res.status_code == 200

    with app.app_context():
        sub = db.session.get(TelegramSubscriber, '1111111')
        assert sub is not None
        assert sub.username == 'johndoe'

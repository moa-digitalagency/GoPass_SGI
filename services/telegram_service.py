import os
import logging
import asyncio
from cryptography.fernet import Fernet
from models import db, TelegramBotConfig, TelegramSubscriber
from datetime import datetime
from telegram import Bot
from flask import current_app

logger = logging.getLogger(__name__)

class TelegramService:
    _cipher_suite = None

    @classmethod
    def get_cipher_suite(cls):
        if cls._cipher_suite is None:
            key = os.environ.get('TELEGRAM_ENCRYPTION_KEY')
            if not key:
                logger.error("TELEGRAM_ENCRYPTION_KEY not set. Encryption unavailable.")
                return None

            if isinstance(key, str):
                key = key.encode()

            cls._cipher_suite = Fernet(key)
        return cls._cipher_suite

    @classmethod
    def encrypt_token(cls, token):
        if not token: return None
        cipher = cls.get_cipher_suite()
        if not cipher: return None
        return cipher.encrypt(token.encode()).decode()

    @classmethod
    def decrypt_token(cls, encrypted_token):
        if not encrypted_token: return None
        cipher = cls.get_cipher_suite()
        if not cipher: return None
        try:
            return cipher.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    @classmethod
    async def get_bot(cls):
        config = TelegramBotConfig.query.first()
        if not config or not config.is_active or not config.bot_token:
            return None

        token = cls.decrypt_token(config.bot_token)
        if not token:
            return None

        return Bot(token=token)

    @classmethod
    def register_subscriber(cls, chat_id, username, first_name):
        subscriber = db.session.get(TelegramSubscriber, str(chat_id))
        if not subscriber:
            subscriber = TelegramSubscriber(
                chat_id=str(chat_id),
                username=username,
                first_name=first_name,
                status='PENDING',
                requested_at=datetime.utcnow(),
                subscriptions=[]
            )
            db.session.add(subscriber)
            db.session.commit()
            return subscriber, True # Created
        return subscriber, False # Existed

    @classmethod
    def approve_subscriber(cls, chat_id, approved_by_user_id, role_label, subscriptions):
        subscriber = db.session.get(TelegramSubscriber, str(chat_id))
        if not subscriber:
            return False, "Subscriber not found"

        subscriber.status = 'APPROVED'
        subscriber.approved_by = approved_by_user_id
        subscriber.approved_at = datetime.utcnow()
        subscriber.role_label = role_label
        subscriber.subscriptions = subscriptions
        db.session.commit()

        try:
            cls.send_message_sync(chat_id, "✅ *Accès Validé*. Vous recevrez désormais les alertes.")
        except Exception as e:
            logger.error(f"Failed to send approval message: {e}")

        return True, "Approved"

    @classmethod
    def revoke_subscriber(cls, chat_id):
        subscriber = db.session.get(TelegramSubscriber, str(chat_id))
        if not subscriber:
            return False, "Subscriber not found"

        subscriber.status = 'REVOKED'
        subscriber.subscriptions = []
        db.session.commit()

        try:
            cls.send_message_sync(chat_id, "⛔ *Votre accès a été révoqué*.")
        except Exception as e:
            logger.error(f"Failed to send revocation message: {e}")

        return True, "Revoked"

    @classmethod
    def update_config(cls, token, is_active=True):
        config = TelegramBotConfig.query.first()
        if not config:
            config = TelegramBotConfig()
            db.session.add(config)

        config.bot_token = cls.encrypt_token(token)
        config.is_active = is_active
        config.updated_at = datetime.utcnow()
        db.session.commit()
        return True

    @classmethod
    def send_message_sync(cls, chat_id, text):
        asyncio.run(cls._send_message_async(chat_id, text))

    @classmethod
    async def _send_message_async(cls, chat_id, text):
        bot = await cls.get_bot()
        if bot:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')

    @classmethod
    def send_notification(cls, event_type, message_markdown):
        subscribers = TelegramSubscriber.query.filter_by(status='APPROVED').all()

        targets = []
        for sub in subscribers:
            if sub.subscriptions and event_type in sub.subscriptions:
                targets.append(sub.chat_id)

        if not targets:
            return 0

        asyncio.run(cls._broadcast(targets, message_markdown))
        return len(targets)

    @classmethod
    async def _broadcast(cls, chat_ids, text):
        bot = await cls.get_bot()
        if not bot:
            return

        for chat_id in chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send to {chat_id}: {e}")

    @classmethod
    def test_connection(cls):
        try:
            return asyncio.run(cls._test_connection_async())
        except Exception as e:
             return False, str(e)

    @classmethod
    async def _test_connection_async(cls):
        bot = await cls.get_bot()
        if not bot:
             return False, "Bot not configured or inactive"

        me = await bot.get_me()
        return True, f"Connected as @{me.username}"

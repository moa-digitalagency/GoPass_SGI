from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from services import TelegramService
from models import TelegramSubscriber, TelegramBotConfig, db
from telegram import Update
from datetime import datetime
import asyncio
import json

telegram_bp = Blueprint('telegram', __name__)

@telegram_bp.route('/dashboard/telegram')
@login_required
def index():
    if current_user.role != 'admin':
        return render_template('errors/403.html'), 403

    config = TelegramBotConfig.query.first()
    pending = TelegramSubscriber.query.filter_by(status='PENDING').all()
    approved = TelegramSubscriber.query.filter_by(status='APPROVED').all()

    return render_template('dashboard/telegram.html', config=config, pending=pending, approved=approved)

@telegram_bp.route('/api/telegram/config', methods=['POST'])
@login_required
def update_config():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    token = request.form.get('bot_token')
    is_active = request.form.get('is_active') == 'true'

    if not token: # If just toggling active
        config = TelegramBotConfig.query.first()
        if config and config.bot_token:
            config.is_active = is_active
            config.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Configuration updated'})
        return jsonify({'error': 'Token required'}), 400

    TelegramService.update_config(token, is_active)
    return jsonify({'message': 'Configuration saved'})

@telegram_bp.route('/api/telegram/test', methods=['POST'])
@login_required
def test_connection():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    success, message = TelegramService.test_connection()
    return jsonify({'success': success, 'message': message})

@telegram_bp.route('/api/telegram/approve/<chat_id>', methods=['POST'])
@login_required
def approve_subscriber(chat_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    role_label = data.get('role_label', 'User')
    subscriptions = data.get('subscriptions', []) # List of strings

    success, msg = TelegramService.approve_subscriber(chat_id, current_user.id, role_label, subscriptions)
    if success:
        return jsonify({'message': msg})
    return jsonify({'error': msg}), 400

@telegram_bp.route('/api/telegram/revoke/<chat_id>', methods=['POST'])
@login_required
def revoke_subscriber(chat_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    success, msg = TelegramService.revoke_subscriber(chat_id)
    if success:
        return jsonify({'message': msg})
    return jsonify({'error': msg}), 400

@telegram_bp.route('/api/telegram/webhook', methods=['POST'])
def webhook():
    # This endpoint is called by Telegram.
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, None)

        if not update or not update.message or not update.message.text:
            return jsonify({'status': 'ok'})

        text = update.message.text
        chat_id = update.message.chat_id
        username = update.message.from_user.username
        first_name = update.message.from_user.first_name

        if text.strip() == '/start':
            subscriber, created = TelegramService.register_subscriber(chat_id, username, first_name)

            if created:
                TelegramService.send_message_sync(chat_id, f"🔒 *Demande d'accès enregistrée*.\nIdentifiant: `{chat_id}`\nEn attente de validation par l'Administrateur SGI-GP.")
            elif subscriber.status == 'PENDING':
                TelegramService.send_message_sync(chat_id, "⏳ Votre demande est toujours en attente de validation.")
            elif subscriber.status == 'APPROVED':
                TelegramService.send_message_sync(chat_id, "✅ Votre accès est déjà validé.")
            elif subscriber.status == 'REVOKED':
                TelegramService.send_message_sync(chat_id, "⛔ Votre accès a été révoqué.")

        return jsonify({'status': 'ok'})
    except Exception as e:
        current_app.logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

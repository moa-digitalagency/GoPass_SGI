"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for Mock Payment Service
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import time
import uuid

class MockPaymentService:
    @staticmethod
    def process_payment(provider, data):
        """
        Simulates payment processing with latency and validation rules.

        Args:
            provider (str): 'STRIPE' or 'MOBILE_MONEY'
            data (dict): Contains 'card_number' or 'mobile_number'

        Returns:
            dict: { 'success': bool, 'transaction_id': str, 'message': str }
        """
        # Simulate network latency
        time.sleep(2)

        if provider == 'STRIPE':
            card_number = data.get('card_number', '').replace(' ', '')
            if card_number.startswith('4242'):
                return {
                    'success': True,
                    'transaction_id': f"DEMO-TX-{uuid.uuid4().hex[:8].upper()}",
                    'message': "Paiement réussi"
                }
            elif card_number.startswith('4000'):
                return {
                    'success': False,
                    'transaction_id': None,
                    'message': "Fonds insuffisants"
                }
            else:
                # Default behavior for other cards in demo?
                # Prompt implies specific rules. Let's fail by default to encourage using test numbers.
                return {
                    'success': False,
                    'transaction_id': None,
                    'message': "Carte non reconnue en mode démo (Utilisez 4242...)"
                }

        elif provider == 'MOBILE_MONEY':
            phone_number = data.get('mobile_number', '').replace(' ', '')
            if phone_number == '0990000000':
                return {
                    'success': True,
                    'transaction_id': f"DEMO-MM-{uuid.uuid4().hex[:8].upper()}",
                    'message': "Paiement réussi"
                }
            elif phone_number == '0999999999':
                return {
                    'success': False,
                    'transaction_id': None,
                    'message': "Délai dépassé (Timeout simulé)"
                }
            else:
                 return {
                    'success': False,
                    'transaction_id': None,
                    'message': "Numéro non reconnu en mode démo (Utilisez 0990000000)"
                }

        return {
            'success': False,
            'transaction_id': None,
            'message': "Fournisseur de paiement inconnu"
        }

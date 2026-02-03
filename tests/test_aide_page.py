import unittest
from app import create_app

class AidePageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_aide_page_loads(self):
        response = self.client.get('/aide')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')

        # Check for title
        self.assertIn("Centre d'Aide (FAQ)", content)

        # Check for categories
        self.assertIn("Achat & Paiement", content)
        self.assertIn("Utilisation du E-GoPass", content)
        self.assertIn("Problèmes Techniques", content)

        # Check for questions
        self.assertIn("Quels sont les moyens de paiement acceptés ?", content)
        self.assertIn("Dois-je imprimer mon QR Code ?", content)

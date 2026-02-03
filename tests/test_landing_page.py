import unittest
from app import create_app

class LandingPageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_landing_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')

        # Check for the app name
        self.assertIn("SGI-GP RDC", content)

        # Check for the hero title parts (Note: HTML uses CSS uppercase, but source is Mixed Case)
        self.assertIn("Portail Officiel du", content)
        self.assertIn("E-GoPass", content)

        # Check for IDEF text
        self.assertIn("IDEF", content)
        # Check for specific new elements
        self.assertIn("Tarifs GoPass", content)
        self.assertIn("Accès Agent", content)

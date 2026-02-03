import unittest
from app import create_app

class LandingPageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_landing_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check for the app name
        self.assertIn(b"SGI-GP RDC", response.data)
        # Check for the hero title "PRÊT À" (UTF-8 bytes: PR\xc3\x8aT \xc3\x80)
        # PRÊT À
        # Ê = \xc3\x8a
        # À = \xc3\x80
        self.assertIn(b"PR\xc3\x8aT \xc3\x80", response.data)
        # Check for IDEF text
        self.assertIn(b"IDEF", response.data)

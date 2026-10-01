import unittest
import json
import urllib.request
import urllib.parse
from whatsapp_engine import process_whatsapp_query, load_latest_data

class TestWhatsAppEngine(unittest.TestCase):
    def setUp(self):
        self.data = load_latest_data()
        self.assertIsNotNone(self.data, "latest_data.json must exist for tests to run")

    def test_due_tomorrow(self):
        reply = process_whatsapp_query("what is due tomorrow?")
        self.assertIn("DU 5th Grade", reply)
        self.assertIn("Due Tomorrow", reply)

    def test_upcoming_tests(self):
        reply = process_whatsapp_query("what tests are coming up?")
        self.assertIn("Upcoming Tests", reply)
        self.assertIn("Surah Al-Maarij", reply)

    def test_ixl_summary(self):
        reply = process_whatsapp_query("what are the IXL homeworks?")
        self.assertIn("Weekly IXL", reply)

    def test_quran_summary(self):
        reply = process_whatsapp_query("what surahs are for review?")
        self.assertIn("Qur'an & Arabic", reply)
        self.assertIn("Main Hifz", reply)
        self.assertIn("Review Surahs", reply)

    def test_spelling_summary(self):
        reply = process_whatsapp_query("spelling list")
        self.assertIn("Weekly Spelling Words", reply)
        self.assertIn("ounce", reply)

    def test_fallback_help(self):
        reply = process_whatsapp_query("hello bot")
        self.assertIn("Ask me anything about weekly homework", reply)

if __name__ == '__main__':
    unittest.main()

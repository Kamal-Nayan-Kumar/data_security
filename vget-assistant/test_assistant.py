import unittest
from assistant import get_response

class TestAssistant(unittest.TestCase):
    def test_login(self):
        res = get_response("how do I login")
        self.assertIn("vget login", res)

    def test_publish(self):
        res = get_response("publish a package")
        self.assertIn("vget publish", res)

    def test_unknown(self):
        res = get_response("blah blah")
        self.assertIn("I'm not sure", res)

if __name__ == "__main__":
    unittest.main()

import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import envdoctor as e


def codes(env, ex):
    return sorted((f["code"], f["key"]) for f in e.diagnose(*[e.parse(x)[0] for x in (env, ex)]))


class T(unittest.TestCase):
    def test_parse(self):
        env, bad = e.parse('export A=1\nB="x # y"\nC=z # c\n# n\n\nbroken line\nD=\n')
        self.assertEqual(env, {"A": "1", "B": "x # y", "C": "z", "D": ""})
        self.assertEqual(bad, [(6, "broken line")])

    def test_missing_extra(self):
        self.assertEqual(codes("A=1\nC=3", "A=\nB="), [("extra", "C"), ("missing", "B")])

    def test_empty_with_default(self):
        self.assertEqual(codes("PORT=", "PORT=3000"), [("empty", "PORT")])
        self.assertEqual(codes("TOKEN=", "TOKEN="), [])

    def test_secret_in_example(self):
        self.assertIn(("leaked-secret", "API_KEY"), codes("API_KEY=x", "API_KEY=abcdef1234567890abcd"))
        self.assertIn(("leaked-secret", "X"), codes("X=1", "X=ghp_" + "a" * 36))
        self.assertEqual(codes("API_KEY=x", "API_KEY=your_api_key_here"), [])
        self.assertEqual(codes("API_KEY=x", "API_KEY="), [])


if __name__ == "__main__":
    unittest.main()

import ast
import unittest

from tools.psm_wma.stage1_v17_request_projection import AuthorityReplayError, _literal


class ProjectionLiteralTest(unittest.TestCase):
    def test_constant_and_add(self):
        node = ast.parse("b'a' + b'b'", mode="eval").body
        self.assertEqual(_literal(node), b"ab")

    def test_name_fails_closed(self):
        node = ast.parse("value", mode="eval").body
        with self.assertRaisesRegex(AuthorityReplayError, "projection_literal"):
            _literal(node)

    def test_call_fails_closed(self):
        node = ast.parse("f()", mode="eval").body
        with self.assertRaisesRegex(AuthorityReplayError, "projection_literal"):
            _literal(node)


if __name__ == "__main__":
    unittest.main()

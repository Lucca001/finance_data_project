import unittest

from src.finance_analysis import normalize_ticker, validate_period


class FinanceAnalysisTest(unittest.TestCase):
    def test_normalize_ticker(self):
        self.assertEqual(normalize_ticker("petr4.sa"), "PETR4.SA")
        self.assertEqual(normalize_ticker(" AAPL "), "AAPL")
        self.assertEqual(normalize_ticker("mglu3"), "MGLU3")

    def test_validate_period(self):
        self.assertEqual(validate_period("1y"), "1y")
        self.assertEqual(validate_period("6mo"), "6mo")
        with self.assertRaises(ValueError):
            validate_period("10anos")


if __name__ == "__main__":
    unittest.main()

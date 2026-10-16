import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze import calculate, read_events
from ingest import ingest


ROOT = Path(__file__).resolve().parents[1]


class Calculations(unittest.TestCase):
    def test_audited_sample(self):
        rows = [calculate(row) for row in read_events(ROOT / "data/msft_events.csv")]
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(r["opening_change_usd"] < 0 for r in rows), 1)
        self.assertEqual(sum(r["closing_change_usd"] < 0 for r in rows), 4)
        self.assertAlmostEqual(rows[0]["opening_change_usd"], 5.59)
        self.assertAlmostEqual(rows[0]["closing_change_usd"], -8.69)
        self.assertAlmostEqual(rows[-1]["opening_change_usd"], -1.01)
        self.assertAlmostEqual(rows[-1]["closing_residual_usd"], -2.25)

    def test_snapshot_is_idempotent(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            source = ROOT / "data/msft_events.csv"
            self.assertIsNotNone(ingest(source, folder))
            self.assertIsNone(ingest(source, folder))
            self.assertEqual(len(list(folder.glob("*.csv"))), 1)


if __name__ == "__main__":
    unittest.main()

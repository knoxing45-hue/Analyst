import unittest
from app.services.risk_reward import RiskRewardCalculator, get_pip_size


class TestRiskReward(unittest.TestCase):
    def test_pip_size(self):
        self.assertEqual(get_pip_size("EURUSD"), 0.0001)
        self.assertEqual(get_pip_size("USDJPY"), 0.01)
        self.assertEqual(get_pip_size("XAUUSD"), 0.10)

    def test_calculate_long(self):
        r = RiskRewardCalculator.calculate(
            entry=1.1000, stop_loss=1.0950, take_profit=1.1125,
            account_size=10000, risk_percent=1.0, symbol="EURUSD",
        )
        self.assertEqual(r["risk_amount"], 100.0)
        self.assertEqual(r["risk_pips"], 50)
        self.assertEqual(r["reward_pips"], 125)
        self.assertAlmostEqual(r["rr_ratio"], 2.5, places=2)
        self.assertEqual(r["direction"], "long")

    def test_build_trade_plan(self):
        plan = RiskRewardCalculator.build_trade_plan(
            symbol="EURUSD", market_type="forex",
            entry=1.1000, stop_loss=1.0950,
            take_profits=[1.1050, 1.1100, 1.1125],
            account_size=10000, risk_percent=1.0,
        )
        self.assertEqual(len(plan["targets"]), 3)
        self.assertAlmostEqual(plan["position_lots"], 0.20, places=2)


if __name__ == "__main__":
    unittest.main()

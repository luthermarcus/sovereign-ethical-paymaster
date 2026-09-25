import sqlite3
import os
import time

class EthicalPaymaster:
    def __init__(self, db_path="treasury_metrics.db", tax_bps=150, max_fee_ratio=0.15):
        self.db_path = db_path
        self.tax_bps = tax_bps
        self.max_fee_ratio = max_fee_ratio
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path) if '/' in self.db_path else '.', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gas_sponsorship_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                sender TEXT,
                asset_amount REAL,
                tax_deducted REAL,
                gas_sponsored REAL,
                execution_status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def evaluate_and_sponsor(self, sender: str, amount: float, gas_cost: float) -> tuple[bool, str, float]:
        if amount <= 0:
            return False, "Invalid asset value.", 0.0
        if gas_cost > (amount * self.max_fee_ratio):
            self._log(sender, amount, 0.0, 0.0, "REJECTED_PARASITIC_OVERHEAD")
            return False, f"Fee rejected: gas cost (${gas_cost:.2f}) exceeds {int(self.max_fee_ratio*100)}% ceiling.", amount
        tax_deducted = (amount * self.tax_bps) / 10000
        net_received = amount - tax_deducted
        self._log(sender, amount, tax_deducted, gas_cost, "SPONSORED_APPROVED")
        return True, "Transaction sponsored successfully via ecosystem tax pool.", net_received

    def _log(self, sender, amount, tax, gas, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gas_sponsorship_ledger (timestamp, sender, asset_amount, tax_deducted, gas_sponsored, execution_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (time.time(), sender, amount, tax, gas, status))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    engine = EthicalPaymaster()
    ok, note, net = engine.evaluate_and_sponsor("0xExternalDevTest", 25.0, 0.75)
    print(f"[Standalone Test] {note} | Net: ${net:.2f}")

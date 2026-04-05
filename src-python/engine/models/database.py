# src-python/engine/models/database.py
import sqlite3
from typing import Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def init(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def close(self):
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS fund_info (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            fund_type TEXT NOT NULL,
            invest_type TEXT NOT NULL,
            t_plus TEXT NOT NULL,
            list_date TEXT,
            is_excluded INTEGER DEFAULT 0,
            has_market_data INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS daily_quote (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL, close REAL, high REAL, low REAL,
            volume REAL, amount REAL,
            nav REAL, premium_rate REAL,
            prev_close REAL,
            is_suspended INTEGER DEFAULT 0,
            suspended_days INTEGER DEFAULT 0,
            PRIMARY KEY (code, date),
            FOREIGN KEY (code) REFERENCES fund_info(code)
        );
        CREATE TABLE IF NOT EXISTS fund_nav_history (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            nav REAL NOT NULL,
            PRIMARY KEY (code, date),
            FOREIGN KEY (code) REFERENCES fund_info(code)
        );
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS screening_result (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            score REAL,
            consecutive_days INTEGER,
            passed INTEGER,
            buy_price REAL,
            tp_price REAL, sl_price REAL,
            details TEXT,
            PRIMARY KEY (code, date)
        );
        CREATE TABLE IF NOT EXISTS scoring_result (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            total_score REAL,
            trend_score REAL, momentum_score REAL,
            volatility_score REAL, volume_score REAL,
            signal TEXT,
            details TEXT,
            PRIMARY KEY (code, date)
        );
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase TEXT, start_time TEXT, end_time TEXT,
            fund_count INTEGER, hit_count INTEGER,
            status TEXT, error TEXT
        );
        """)
        self.conn.commit()

    def get_tables(self) -> list[str]:
        c = self.conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [r[0] for r in c.fetchall()]

    def upsert_fund_info(self, funds: list[dict]):
        c = self.conn.cursor()
        for f in funds:
            record = dict(f)
            record.setdefault("has_market_data", 1)
            c.execute("""
                INSERT INTO fund_info (code,name,fund_type,invest_type,t_plus,list_date,is_excluded,has_market_data)
                VALUES (:code,:name,:fund_type,:invest_type,:t_plus,:list_date,:is_excluded,:has_market_data)
                ON CONFLICT(code) DO UPDATE SET
                    name=excluded.name, fund_type=excluded.fund_type,
                    invest_type=excluded.invest_type, t_plus=excluded.t_plus,
                    list_date=excluded.list_date, is_excluded=excluded.is_excluded,
                    has_market_data=excluded.has_market_data
            """, record)
        self.conn.commit()

    def get_fund_info(self, code: str) -> Optional[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM fund_info WHERE code=?", (code,))
        row = c.fetchone()
        return dict(row) if row else None

    def get_all_active_funds(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM fund_info WHERE is_excluded=0")
        return [dict(r) for r in c.fetchall()]

    def get_all_funds_with_market_data(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM fund_info WHERE is_excluded=0 AND has_market_data=1")
        return [dict(r) for r in c.fetchall()]

    def upsert_daily_quotes(self, quotes: list[dict]):
        c = self.conn.cursor()
        for q in quotes:
            c.execute("""
                INSERT INTO daily_quote
                    (code,date,open,close,high,low,volume,amount,
                     nav,premium_rate,prev_close,is_suspended,suspended_days)
                VALUES (:code,:date,:open,:close,:high,:low,:volume,:amount,
                        :nav,:premium_rate,:prev_close,:is_suspended,:suspended_days)
                ON CONFLICT(code,date) DO UPDATE SET
                    open=excluded.open, close=excluded.close,
                    high=excluded.high, low=excluded.low,
                    volume=excluded.volume, amount=excluded.amount,
                    nav=excluded.nav, premium_rate=excluded.premium_rate,
                    prev_close=excluded.prev_close,
                    is_suspended=excluded.is_suspended,
                    suspended_days=excluded.suspended_days
            """, q)
        self.conn.commit()

    def get_daily_quotes(self, code: str, start: str, end: str) -> list[dict]:
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM daily_quote WHERE code=? AND date>=? AND date<=? ORDER BY date",
            (code, start, end)
        )
        return [dict(r) for r in c.fetchall()]

    def get_latest_date(self, code: str) -> Optional[str]:
        c = self.conn.cursor()
        c.execute("SELECT MAX(date) FROM daily_quote WHERE code=?", (code,))
        row = c.fetchone()
        return row[0] if row and row[0] else None

    def upsert_fund_nav_history(self, rows: list[dict]):
        c = self.conn.cursor()
        for row in rows:
            c.execute(
                """
                INSERT INTO fund_nav_history (code, date, nav)
                VALUES (:code, :date, :nav)
                ON CONFLICT(code, date) DO UPDATE SET nav=excluded.nav
                """,
                row,
            )
        self.conn.commit()

    def get_fund_nav_history(self, code: str, start: str, end: str) -> list[dict]:
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM fund_nav_history WHERE code=? AND date>=? AND date<=? ORDER BY date",
            (code, start, end),
        )
        return [dict(r) for r in c.fetchall()]

    def _update_nav(self, code: str, date: str, nav: float):
        """仅更新净值，如果记录不存在则不插入"""
        c = self.conn.cursor()
        c.execute("SELECT close FROM daily_quote WHERE code=? AND date=?", (code, date))
        row = c.fetchone()
        if row:
            close_price = row[0]
            premium_rate = None
            if nav > 0:
                premium_rate = (close_price - nav) / nav
            c.execute(
                "UPDATE daily_quote SET nav=?, premium_rate=? WHERE code=? AND date=?",
                (nav, premium_rate, code, date)
            )
        self.conn.commit()

    def update_has_market_data(self, code: str, value: int):
        if value not in (0, 1):
            raise ValueError(f"has_market_data must be 0 or 1, got {value}")
        c = self.conn.cursor()
        c.execute("UPDATE fund_info SET has_market_data=? WHERE code=?", (value, code))
        self.conn.commit()

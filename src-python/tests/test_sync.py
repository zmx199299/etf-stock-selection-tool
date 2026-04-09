# src-python/tests/test_sync.py
import os
import tempfile
import pytest
import pandas as pd
from engine.sync import DataSyncPipeline
from engine.models.database import Database


class MockAkshareSource:
    """模拟 akshare 数据源，不需要真实联网"""

    def fetch_fund_list(self):
        return [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2012-05-28",
                "is_excluded": 0,
            },
            {
                "code": "159915",
                "name": "创业板ETF",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2010-02-11",
                "is_excluded": 0,
            },
            {
                "code": "510500",
                "name": "中证500ETF",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2013-02-06",
                "is_excluded": 0,
            },
            {
                "code": "513050",
                "name": "中概互联网ETF",
                "fund_type": "ETF",
                "invest_type": "跨境型(QDII)",
                "t_plus": "T+0",
                "list_date": "2014-01-16",
                "is_excluded": 0,
            },
        ]

    def fetch_daily_quotes(self, code: str, start_date: str = None):
        n = 30
        dates = pd.date_range(end="2026-03-28", periods=n)
        base = 4.0 if code == "510300" else 2.0
        return [
            {
                "date": str(d)[:10],
                "open": base + i * 0.01,
                "close": base + i * 0.01 + 0.02,
                "high": base + i * 0.01 + 0.05,
                "low": base + i * 0.01 - 0.03,
                "volume": 100000 + i * 1000,
                "amount": (100000 + i * 1000) * base,
            }
            for i, d in enumerate(dates)
        ]

    def fetch_nav(self, code: str, start_date: str = None):
        return [{"date": "2026-03-28", "nav": 4.118}]


@pytest.fixture
def mock_env(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.init()
    yield {"db": db, "source": MockAkshareSource()}
    db.close()


def test_sync_fund_list(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    pipeline.sync_fund_list()
    funds = mock_env["db"].get_all_active_funds()
    assert len(funds) == 4
    assert funds[0]["code"] == "510300"
    assert funds[0]["t_plus"] == "T+1"


def test_sync_daily_quotes(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    pipeline.sync_fund_list()
    pipeline.sync_daily_quotes_for_all()
    quotes = mock_env["db"].get_daily_quotes("510300", "2026-03-01", "2026-03-28")
    assert len(quotes) == 28
    assert quotes[-1]["close"] == pytest.approx(4.0 + 29 * 0.01 + 0.02, abs=0.001)


def test_sync_nav(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    pipeline.sync_fund_list()
    pipeline.sync_daily_quotes_for_all()
    pipeline.sync_nav_for_all()
    quotes = mock_env["db"].get_daily_quotes("510300", "2026-03-28", "2026-03-28")
    assert len(quotes) == 1
    assert quotes[0]["nav"] == pytest.approx(4.118, abs=0.001)
    assert quotes[0]["premium_rate"] is not None


def test_sync_all(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    result = pipeline.sync_all()
    assert "funds_synced" in result
    assert "quotes_synced" in result
    assert result["funds_synced"] == 4
    assert result["quotes_synced"] > 0


def test_sync_skips_excluded_funds(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    pipeline.sync_fund_list()
    funds = mock_env["db"].get_all_active_funds()
    codes = [f["code"] for f in funds]
    assert "510300" in codes
    assert "513050" in codes


class NavExplodingSource:
    """模拟某些基金的 fetch_nav 会抛异常（如 NaN 导致数据库约束错误）"""

    def __init__(self, exploding_codes: set):
        self.exploding_codes = exploding_codes

    def fetch_fund_list(self):
        return [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2012-05-28",
                "is_excluded": 0,
            },
            {
                "code": "159915",
                "name": "创业板ETF",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2010-02-11",
                "is_excluded": 0,
            },
            {
                "code": "510500",
                "name": "中证500ETF",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2013-02-06",
                "is_excluded": 0,
            },
        ]

    def fetch_daily_quotes(self, code: str, start_date: str = None):
        return [
            {
                "date": "2026-04-01",
                "open": 4.0,
                "close": 4.1,
                "high": 4.2,
                "low": 3.9,
                "volume": 10000,
                "amount": 41000,
            }
        ]

    def fetch_nav(self, code: str, start_date: str = None):
        if code in self.exploding_codes:
            # 模拟因 NaN 值导致的数据库写入异常
            raise Exception(
                f"NOT NULL constraint failed: fund_nav_history.nav (code={code})"
            )
        return [{"date": "2026-04-01", "nav": 4.118}]


def test_sync_nav_resilient_to_per_fund_errors(tmp_path):
    """sync_nav_for_all() 某只基金出错时不应崩溃整个 NAV 同步"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.init()

    # 159915 的 NAV 会抛异常，但其他基金应继续同步
    source = NavExplodingSource(exploding_codes={"159915"})
    pipeline = DataSyncPipeline(db, source)
    pipeline.sync_fund_list()
    pipeline.sync_daily_quotes_for_all()

    # 不应崩溃
    nav_count = pipeline.sync_nav_for_all()

    # 应该至少同步了 510300 和 510500 的 NAV（159915 失败被跳过）
    assert nav_count >= 2

    # 验证正常基金的 NAV 确实写入了
    nav_history = db.get_fund_nav_history("510300", "2026-04-01", "2026-04-01")
    assert len(nav_history) == 1
    assert nav_history[0]["nav"] == pytest.approx(4.118, abs=0.001)

    db.close()


class AlwaysFailSource:
    """模拟所有数据源都失败的情况"""

    def __init__(self):
        self.fetch_daily_quotes_call_count = 0

    def fetch_fund_list(self):
        return [
            {
                "code": f"ETF{i:03d}",
                "name": f"测试ETF{i}",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2020-01-01",
                "is_excluded": 0,
            }
            for i in range(50)  # 50只基金，足够触发早期终止
        ]

    def fetch_daily_quotes(self, code: str, start_date: str = None):
        self.fetch_daily_quotes_call_count += 1
        return []  # 模拟所有源都失败（返回空 = 无数据）

    def fetch_nav(self, code: str, start_date: str = None):
        return []


class PartialFailSource:
    """前 N 只基金失败，之后恢复"""

    def __init__(self, fail_count: int):
        self.fail_count = fail_count
        self.call_count = 0

    def fetch_fund_list(self):
        return [
            {
                "code": f"ETF{i:03d}",
                "name": f"测试ETF{i}",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "2020-01-01",
                "is_excluded": 0,
            }
            for i in range(30)
        ]

    def fetch_daily_quotes(self, code: str, start_date: str = None):
        self.call_count += 1
        if self.call_count <= self.fail_count:
            return []  # 前 N 只失败
        return [
            {
                "date": "2026-04-01",
                "open": 4.0,
                "close": 4.1,
                "high": 4.2,
                "low": 3.9,
                "volume": 10000,
                "amount": 41000,
            }
        ]

    def fetch_nav(self, code: str, start_date: str = None):
        return []


def test_early_abort_on_consecutive_failures(tmp_path):
    """当连续 max_consecutive_failures 只基金都无数据时，应提前终止同步"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.init()

    source = AlwaysFailSource()
    pipeline = DataSyncPipeline(db, source)
    pipeline.sync_fund_list()

    # 设置连续失败阈值为 10，总共 50 只基金
    total = pipeline.sync_daily_quotes_for_all(max_consecutive_failures=10)

    # 应该在尝试约 10 只后提前终止，而非全部 50 只
    assert source.fetch_daily_quotes_call_count <= 15  # 留一些余量
    assert source.fetch_daily_quotes_call_count < 50  # 关键：不应尝试全部
    assert total == 0

    db.close()


def test_no_early_abort_when_intermittent_failures(tmp_path):
    """当失败不连续（中间有成功的）时，不应提前终止"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.init()

    # 前 5 只失败，之后恢复
    source = PartialFailSource(fail_count=5)
    pipeline = DataSyncPipeline(db, source)
    pipeline.sync_fund_list()

    # max_consecutive_failures=10，前 5 只失败不应触发终止
    total = pipeline.sync_daily_quotes_for_all(max_consecutive_failures=10)

    # 应该处理全部 30 只基金
    assert source.call_count == 30
    assert total > 0  # 后 25 只应有数据

    db.close()


def test_early_abort_default_threshold(tmp_path):
    """不传 max_consecutive_failures 参数时使用默认值（仍能早期终止）"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.init()

    source = AlwaysFailSource()
    pipeline = DataSyncPipeline(db, source)
    pipeline.sync_fund_list()

    # 使用默认阈值
    total = pipeline.sync_daily_quotes_for_all()

    # 默认阈值应该阻止尝试全部 50 只
    assert source.fetch_daily_quotes_call_count < 50
    assert total == 0

    db.close()

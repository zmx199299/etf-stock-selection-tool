# src-python/tests/test_engine_startup.py
"""
测试 Python 引擎启动流程（main.py 中的 main 函数）。
核心验证：
1. main.py 能正确 import（类名正确）
2. Database 被正确初始化（init() 被调用），引擎不会崩溃
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from engine.models.database import Database


class TestDatabaseInitRequired:
    """验证 Database 必须调用 init() 后才能使用"""

    def test_database_without_init_raises_on_query(self):
        """确认 Database 在未调用 init() 时查询会失败（self.conn 为 None）"""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            db = Database(db_path)
            # 不调用 db.init()
            with pytest.raises(AttributeError):
                db.get_all_funds_with_market_data()
        finally:
            os.unlink(db_path)

    def test_database_with_init_succeeds_on_query(self):
        """确认 Database 在调用 init() 后查询正常"""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            db = Database(db_path)
            db.init()
            # 这不应该抛异常
            result = db.get_all_funds_with_market_data()
            assert isinstance(result, list)
            db.close()
        finally:
            os.unlink(db_path)


class TestMainModule:
    """验证 main.py 模块的正确性"""

    def test_main_module_imports_successfully(self):
        """main.py 必须能成功 import，不能有 ImportError"""
        # 如果 main.py 中引用了不存在的类名（如 AkshareDataSource），
        # 这个 import 会失败
        try:
            # 需要先清除可能的缓存
            if "main" in sys.modules:
                del sys.modules["main"]
            import main

            # 验证 main 函数存在
            assert callable(main.main)
        except ImportError as e:
            pytest.fail(f"main.py import 失败: {e}")

    def test_main_initializes_db_before_use(self):
        """main() 中 Database 必须在查询前调用 init()"""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            # 清除模块缓存确保使用最新代码
            if "main" in sys.modules:
                del sys.modules["main"]
            from main import main

            app_dir = os.path.dirname(db_path)

            # patch 掉外部依赖
            with (
                patch("main.os.path.expanduser", return_value=app_dir),
                patch("main.os.path.join", return_value=db_path),
                patch("main.create_real_server") as mock_server_factory,
            ):
                mock_server = MagicMock()
                mock_server_factory.return_value = mock_server

                # 如果 db.init() 没被调用，这里会抛出 AttributeError
                # 因为 self.conn 是 None，无法执行 SQL 查询
                main()

                # 验证 server.run_stdio() 被调用（说明启动正常完成）
                mock_server.run_stdio.assert_called_once()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestBackgroundSyncThreadSafety:
    """验证后台同步线程使用独立的数据库连接和数据源"""

    def test_background_sync_creates_own_db_and_source(self):
        """background_sync 应在内部创建自己的 Database 和 AkshareSource 实例"""
        if "main" in sys.modules:
            del sys.modules["main"]
        from main import background_sync

        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            with (
                patch("main.Database") as mock_db_class,
                patch("main.AkshareSource") as mock_source_class,
                patch("main.DataSyncPipeline") as mock_pipeline_class,
            ):
                mock_db_instance = MagicMock()
                mock_db_class.return_value = mock_db_instance
                mock_source_instance = MagicMock()
                mock_source_class.return_value = mock_source_instance
                mock_pipeline = MagicMock()
                mock_pipeline_class.return_value = mock_pipeline

                background_sync(db_path)

                mock_db_class.assert_called_once_with(db_path)
                mock_db_instance.init.assert_called_once()
                mock_source_class.assert_called_once()
                mock_pipeline_class.assert_called_once_with(
                    mock_db_instance, mock_source_instance
                )
                mock_pipeline.sync_all.assert_called_once_with(limit_days=60)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestDatabaseHasDailyQuotes:
    """验证 Database.has_daily_quotes() 方法"""

    def test_returns_false_on_empty_db(self, tmp_path):
        """空数据库应返回 False"""
        db = Database(str(tmp_path / "test.db"))
        db.init()
        assert db.has_daily_quotes() is False
        db.close()

    def test_returns_true_after_insert(self, tmp_path):
        """插入日线数据后应返回 True"""
        db = Database(str(tmp_path / "test.db"))
        db.init()
        db.upsert_fund_info(
            [
                {
                    "code": "510300",
                    "name": "沪深300ETF",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "2020-01-01",
                    "is_excluded": 0,
                }
            ]
        )
        db.upsert_daily_quotes(
            [
                {
                    "code": "510300",
                    "date": "2026-04-01",
                    "open": 4.0,
                    "close": 4.1,
                    "high": 4.2,
                    "low": 3.9,
                    "volume": 10000,
                    "amount": 41000,
                    "nav": None,
                    "premium_rate": None,
                    "prev_close": None,
                    "is_suspended": 0,
                    "suspended_days": 0,
                }
            ]
        )
        assert db.has_daily_quotes() is True
        db.close()

    def test_fund_info_without_daily_quotes_returns_false(self, tmp_path):
        """有基金列表但无日线数据时应返回 False — 这是 v0.0.13 的核心 bug 场景"""
        db = Database(str(tmp_path / "test.db"))
        db.init()
        db.upsert_fund_info(
            [
                {
                    "code": "510300",
                    "name": "沪深300ETF",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "2020-01-01",
                    "is_excluded": 0,
                },
                {
                    "code": "159915",
                    "name": "创业板ETF",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "2020-01-01",
                    "is_excluded": 0,
                },
            ]
        )
        assert db.has_daily_quotes() is False
        db.close()

    def test_fund_info_without_daily_quotes_returns_false(self, tmp_path):
        """有基金列表但无日线数据时应返回 False — 这是 v0.0.13 的核心 bug 场景"""
        db = Database(str(tmp_path / "test.db"))
        db.init()
        db.upsert_fund_info(
            [
                {
                    "code": "510300",
                    "name": "沪深300ETF",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "2020-01-01",
                    "is_excluded": 0,
                },
                {
                    "code": "159915",
                    "name": "创业板ETF",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "2020-01-01",
                    "is_excluded": 0,
                },
            ]
        )
        assert db.has_daily_quotes() is False
        db.close()


class TestBackgroundSyncTrigger:
    """验证后台同步的触发条件：基于 daily_quote 是否为空"""

    def test_sync_triggers_when_fund_info_exists_but_no_daily_quotes(self, tmp_path):
        """fund_info 有数据但 daily_quote 为空时，应触发后台同步"""
        if "main" in sys.modules:
            del sys.modules["main"]
        from main import main

        db_path = str(tmp_path / "test.db")
        app_dir = str(tmp_path)

        # 预先创建数据库并插入基金列表（模拟 v0.0.12 遗留状态）
        db = Database(db_path)
        db.init()
        db.upsert_fund_info(
            [
                {
                    "code": "510300",
                    "name": "沪深300ETF",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "2020-01-01",
                    "is_excluded": 0,
                },
            ]
        )
        db.close()

        with (
            patch("main.os.path.expanduser", return_value=app_dir),
            patch("main.os.path.join", return_value=db_path),
            patch("main.os.makedirs"),
            patch("main.AkshareSource") as mock_source_class,
            patch("main.create_real_server") as mock_server_factory,
            patch("main.threading.Thread") as mock_thread_class,
        ):
            mock_server = MagicMock()
            mock_server_factory.return_value = mock_server
            mock_thread = MagicMock()
            mock_thread_class.return_value = mock_thread

            main()

            # 关键断言：后台同步线程应该被创建并启动
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()


class TestSyncNeedsRetry:
    """验证部分同步失败后的重试检测"""

    def test_needs_sync_when_coverage_too_low(self, tmp_path):
        """有基金列表 1754 只但只有 500 只有日线数据时，应判定需要重新同步"""
        db = Database(str(tmp_path / "test.db"))
        db.init()

        # 插入 10 只基金
        funds = []
        for i in range(10):
            funds.append(
                {
                    "code": f"5103{i:02d}",
                    "name": f"测试ETF{i}",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "",
                    "is_excluded": 0,
                    "has_market_data": 1,
                }
            )
        db.upsert_fund_info(funds)

        # 只给 3 只基金插入日线数据（30% 覆盖率）
        for i in range(3):
            db.upsert_daily_quotes(
                [
                    {
                        "code": f"5103{i:02d}",
                        "date": "2026-04-01",
                        "open": 4.0,
                        "close": 4.1,
                        "high": 4.2,
                        "low": 3.9,
                        "volume": 1000,
                        "amount": 4100,
                        "nav": None,
                        "premium_rate": None,
                        "prev_close": None,
                        "is_suspended": 0,
                        "suspended_days": 0,
                    }
                ]
            )

        # 30% 覆盖率 < 80% 阈值，应该需要重新同步
        assert db.needs_background_sync() is True
        db.close()

    def test_no_sync_when_coverage_sufficient(self, tmp_path):
        """90% 覆盖率应判定不需要重新同步"""
        db = Database(str(tmp_path / "test.db"))
        db.init()

        # 插入 10 只基金
        funds = []
        for i in range(10):
            funds.append(
                {
                    "code": f"5103{i:02d}",
                    "name": f"测试ETF{i}",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "",
                    "is_excluded": 0,
                    "has_market_data": 1,
                }
            )
        db.upsert_fund_info(funds)

        # 给 9 只基金插入日线数据（90% 覆盖率）
        for i in range(9):
            db.upsert_daily_quotes(
                [
                    {
                        "code": f"5103{i:02d}",
                        "date": "2026-04-01",
                        "open": 4.0,
                        "close": 4.1,
                        "high": 4.2,
                        "low": 3.9,
                        "volume": 1000,
                        "amount": 4100,
                        "nav": None,
                        "premium_rate": None,
                        "prev_close": None,
                        "is_suspended": 0,
                        "suspended_days": 0,
                    }
                ]
            )

        # 90% >= 80% 阈值，不需要重新同步
        assert db.needs_background_sync() is False
        db.close()

    def test_sync_needed_when_no_daily_quotes_at_all(self, tmp_path):
        """完全没有日线数据时应需要同步"""
        db = Database(str(tmp_path / "test.db"))
        db.init()
        # 空数据库
        assert db.needs_background_sync() is True
        db.close()

    def test_sync_needed_when_fund_info_exists_but_no_quotes(self, tmp_path):
        """有基金列表但无日线数据，应需要同步"""
        db = Database(str(tmp_path / "test.db"))
        db.init()
        db.upsert_fund_info(
            [
                {
                    "code": "510300",
                    "name": "沪深300ETF",
                    "fund_type": "ETF",
                    "invest_type": "指数型",
                    "t_plus": "T+1",
                    "list_date": "",
                    "is_excluded": 0,
                    "has_market_data": 1,
                }
            ]
        )
        assert db.needs_background_sync() is True
        db.close()

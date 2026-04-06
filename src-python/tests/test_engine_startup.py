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
    """验证后台同步线程使用独立的数据库连接"""

    def test_background_sync_creates_own_db_connection(self):
        """background_sync 应在内部创建自己的 Database 实例，参数应为 db_path 而非 db 对象"""
        if "main" in sys.modules:
            del sys.modules["main"]
        from main import background_sync

        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            source = MagicMock()

            # Patch Database 和 DataSyncPipeline 来验证 background_sync 内部行为
            with (
                patch("main.Database") as mock_db_class,
                patch("main.DataSyncPipeline") as mock_pipeline_class,
            ):
                mock_db_instance = MagicMock()
                mock_db_class.return_value = mock_db_instance
                mock_pipeline = MagicMock()
                mock_pipeline_class.return_value = mock_pipeline

                # 传入 db_path（字符串），background_sync 应在内部创建新 Database
                background_sync(db_path, source)

                # 验证 Database 在后台线程内部被创建并 init
                mock_db_class.assert_called_once_with(db_path)
                mock_db_instance.init.assert_called_once()

                # 验证 DataSyncPipeline 使用的是新建的 db 实例
                mock_pipeline_class.assert_called_once_with(mock_db_instance, source)
                mock_pipeline.sync_all.assert_called_once_with(limit_days=60)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

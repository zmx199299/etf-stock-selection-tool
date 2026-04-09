# src-python/tests/test_sync_all.py
"""sync_all.py 独立数据库生成脚本的单元测试（基于 DataSyncPipeline 重写版）"""

import os
import sys
import tempfile

import pytest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestParseArgs:
    """测试命令行参数解析"""

    def test_no_args_returns_none_output(self):
        """无参数时 output 应为 None（使用默认路径）"""
        from sync_all import parse_args

        args = parse_args([])
        assert args.output is None

    def test_custom_output_path(self):
        """--output 参数应正确解析"""
        from sync_all import parse_args

        args = parse_args(["--output", "/tmp/custom.db"])
        assert args.output == "/tmp/custom.db"


class TestDefaultDbPath:
    """测试默认数据库路径"""

    def test_default_path_ends_with_data_dir(self):
        """默认路径应指向项目根目录的 data/etf_analyzer.db"""
        from sync_all import DEFAULT_DB_PATH

        assert DEFAULT_DB_PATH.endswith(os.path.join("data", "etf_analyzer.db"))


class TestMainFlow:
    """测试 main() 函数的完整流程"""

    def _run_main_with_mock(self, db_path, sync_return=None, sync_side_effect=None):
        """辅助方法：使用 mock 运行 main()"""
        if sync_return is None:
            sync_return = {
                "funds_synced": 10,
                "quotes_synced": 100,
                "nav_updated": 5,
            }

        mock_pipeline = MagicMock()
        if sync_side_effect:
            mock_pipeline.sync_all.side_effect = sync_side_effect
        else:
            mock_pipeline.sync_all.return_value = sync_return

        mock_db = MagicMock()

        with patch("sys.argv", ["sync_all.py", "--output", db_path]):
            with patch("sync_all.Database", return_value=mock_db) as mock_db_cls:
                with patch(
                    "sync_all.AkshareSource", return_value=MagicMock()
                ) as mock_source_cls:
                    with patch(
                        "sync_all.DataSyncPipeline", return_value=mock_pipeline
                    ) as mock_pipeline_cls:
                        from sync_all import main

                        main()

        return mock_db, mock_db_cls, mock_source_cls, mock_pipeline_cls, mock_pipeline

    def test_creates_output_directory(self):
        """main() 应自动创建输出目录（如果不存在）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "nested", "test.db")
            self._run_main_with_mock(db_path)
            assert os.path.isdir(os.path.join(tmpdir, "subdir", "nested"))

    def test_initializes_database(self):
        """main() 应初始化数据库（调用 db.init()）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            mock_db, *_ = self._run_main_with_mock(db_path)
            mock_db.init.assert_called_once()

    def test_calls_sync_all_without_limit(self):
        """main() 应调用 pipeline.sync_all(limit_days=None) 拉取全量历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            *_, mock_pipeline = self._run_main_with_mock(db_path)
            mock_pipeline.sync_all.assert_called_once_with(limit_days=None)

    def test_creates_pipeline_with_db_and_source(self):
        """main() 应用 Database 和 AkshareSource 创建 DataSyncPipeline"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            mock_db, _, mock_source_cls, mock_pipeline_cls, _ = (
                self._run_main_with_mock(db_path)
            )
            # DataSyncPipeline 应该用 db 和 source 实例创建
            mock_pipeline_cls.assert_called_once()
            args = mock_pipeline_cls.call_args
            assert args[0][0] is mock_db  # 第一个参数是 db
            assert args[0][1] is mock_source_cls.return_value  # 第二个参数是 source

    def test_closes_db_after_success(self):
        """同步成功后应关闭数据库连接"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            mock_db, *_ = self._run_main_with_mock(db_path)
            mock_db.close.assert_called_once()

    def test_closes_db_on_error(self):
        """即使 sync_all 抛异常，数据库也应被关闭"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            mock_pipeline = MagicMock()
            mock_pipeline.sync_all.side_effect = RuntimeError("网络异常")
            mock_db = MagicMock()

            with patch("sys.argv", ["sync_all.py", "--output", db_path]):
                with patch("sync_all.Database", return_value=mock_db):
                    with patch("sync_all.AkshareSource", return_value=MagicMock()):
                        with patch(
                            "sync_all.DataSyncPipeline", return_value=mock_pipeline
                        ):
                            from sync_all import main

                            with pytest.raises(RuntimeError, match="网络异常"):
                                main()

            mock_db.close.assert_called_once()

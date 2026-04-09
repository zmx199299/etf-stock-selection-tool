import sys
import logging
import os
import threading
from engine.server import create_real_server
from engine.models.database import Database
from engine.data.akshare_source import AkshareSource
from engine.sync import DataSyncPipeline

# Basic logging to stderr so it doesn't mess up JSON-RPC on stdout
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def background_sync(db_path):
    """如果数据库日线为空，在后台默默进行首次全市场 ETF+LOF 同步（仅最近60天）。
    使用独立的数据库连接和数据源实例，避免与主线程资源冲突。"""
    logger.info("Daily quotes missing. Starting background sync (last 60 days)...")
    try:
        bg_db = Database(db_path)
        bg_db.init()
        bg_source = AkshareSource()
        pipeline = DataSyncPipeline(bg_db, bg_source)
        pipeline.sync_all(limit_days=60)
        logger.info("Background sync completed successfully.")
        bg_db.close()
    except Exception as e:
        logger.error(f"Background sync failed: {e}")


def main():
    # 强制 stderr 行缓冲，确保日志在重定向到文件时即时写入
    sys.stderr.reconfigure(line_buffering=True)

    logger.info("Starting Python ETF Engine...")

    # 1. 确定数据库存放路径（针对生产环境打包后的独立数据目录）
    app_dir = os.path.expanduser("~/.etf-analyzer")
    os.makedirs(app_dir, exist_ok=True)
    db_path = os.path.join(app_dir, "etf_analyzer.db")
    logger.info(f"Using database at: {db_path}")

    # 2. 初始化核心组件
    db = Database(db_path)
    db.init()  # 必须显式调用：连接数据库并创建表结构
    source = AkshareSource()

    # 3. 检查是否需要后台同步（覆盖"部分同步崩溃"的场景：覆盖率不足 80%）
    try:
        if db.needs_background_sync():
            sync_thread = threading.Thread(
                target=background_sync, args=(db_path,), daemon=True
            )
            sync_thread.start()
            logger.info("Background sync thread started.")
        else:
            logger.info("Daily quotes coverage sufficient, skipping background sync.")
    except Exception as e:
        logger.error(f"Failed to check db state: {e}")

    # 4. 创建真正连接到后端模块的 RPC Server
    server = create_real_server(db, source)

    # Block and run on stdio
    logger.info("Engine listening on stdin...")
    server.run_stdio()


if __name__ == "__main__":
    main()

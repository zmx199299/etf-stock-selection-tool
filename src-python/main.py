import sys
import logging
import os
import threading
from engine.server import create_real_server
from engine.models.database import Database
from engine.data.akshare_source import AkshareDataSource
from engine.sync import DataSyncPipeline

# Basic logging to stderr so it doesn't mess up JSON-RPC on stdout
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def background_sync(db, source):
    """如果数据库为空，在后台默默进行首次全市场 ETF+LOF 同步"""
    logger.info("Database is empty. Starting background sync...")
    try:
        pipeline = DataSyncPipeline(db, source)
        pipeline.sync_all()
        logger.info("Background sync completed successfully.")
    except Exception as e:
        logger.error(f"Background sync failed: {e}")

def main():
    logger.info("Starting Python ETF Engine...")
    
    # 1. 确定数据库存放路径（针对生产环境打包后的独立数据目录）
    app_dir = os.path.expanduser("~/.etf-analyzer")
    os.makedirs(app_dir, exist_ok=True)
    db_path = os.path.join(app_dir, "etf_analyzer.db")
    logger.info(f"Using database at: {db_path}")

    # 2. 初始化核心组件
    # Database 的 __init__ 方法里已经自动包含了 self.init_db() 来创建所有空表
    db = Database(db_path)
    source = AkshareDataSource()

    # 3. 检查数据库是否为空，如果为空，启动后台线程进行初始化同步
    try:
        funds = db.get_all_funds_with_market_data()
        if not funds:
            sync_thread = threading.Thread(target=background_sync, args=(db, source), daemon=True)
            sync_thread.start()
    except Exception as e:
        logger.error(f"Failed to check db state: {e}")

    # 4. 创建真正连接到后端模块的 RPC Server
    server = create_real_server(db, source)
    
    # Block and run on stdio
    logger.info("Engine listening on stdin...")
    server.run_stdio()

if __name__ == "__main__":
    main()
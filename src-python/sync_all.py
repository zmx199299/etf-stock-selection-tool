#!/usr/bin/env python3
"""独立数据库生成脚本：基于 DataSyncPipeline 多源容错，生成全量 ETF/LOF 预构建数据库。

用法:
    python sync_all.py                          # 输出到 data/etf_analyzer.db
    python sync_all.py --output /path/to/db     # 自定义输出路径
"""

import argparse
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.models.database import Database
from engine.data.akshare_source import AkshareSource
from engine.sync import DataSyncPipeline


DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "etf_analyzer.db",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="ETF Analyzer 全量数据库生成工具")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"数据库输出路径（默认: {DEFAULT_DB_PATH}）",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()
    db_path = args.output or DEFAULT_DB_PATH

    logger.info("=" * 60)
    logger.info("ETF ANALYZER 全量数据库生成工具")
    logger.info("=" * 60)
    logger.info(f"数据库路径: {db_path}")
    logger.info("口径: 全量场内 ETF+LOF（排除货币/债券），全量历史日线 + NAV")

    # 创建输出目录
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    db = Database(db_path)
    db.init()

    try:
        source = AkshareSource()
        pipeline = DataSyncPipeline(db, source)

        t0 = time.time()
        result = pipeline.sync_all(limit_days=None)
        elapsed = time.time() - t0

        logger.info("=" * 60)
        logger.info("生成完成")
        logger.info(f"  基金列表: {result['funds_synced']} 只")
        logger.info(f"  日线行情: {result['quotes_synced']} 条")
        logger.info(f"  净值记录: {result['nav_updated']} 条")
        logger.info(f"  总耗时: {elapsed:.1f}s ({elapsed / 60:.1f}min)")
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / 1024 / 1024
            logger.info(f"  数据库大小: {size_mb:.1f} MB")
        logger.info("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()

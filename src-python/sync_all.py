#!/usr/bin/env python3
"""一键数据同步脚本：从 akshare 拉取全量数据写入 SQLite"""
import sys
import os
import time
import logging

# 确保可以导入 engine 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.models.database import Database
from engine.data.akshare_source import AkshareSource
from engine.sync import DataSyncPipeline

# 默认数据库路径：项目根目录下的 data/etf_analyzer.db
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "etf_analyzer.db"
)

# 种子基金列表：当 akshare spot API 不可用时作为回退
SEED_FUNDS = [
    # 宽基 ETF
    {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "510500", "name": "中证500ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "159919", "name": "沪深300ETF嘉实", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "510050", "name": "上证50ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "159915", "name": "创业板ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "588000", "name": "科创50ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    # 跨境 ETF (T+0)
    {"code": "513500", "name": "标普500ETF", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "513100", "name": "纳指ETF", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "159920", "name": "恒生ETF", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "513030", "name": "德国30ETF", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    # 行业/主题 ETF
    {"code": "512880", "name": "证券ETF", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512660", "name": "军工ETF", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512480", "name": "半导体ETF", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "515790", "name": "光伏ETF", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512170", "name": "医疗ETF", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    # 商品 ETF (T+0)
    {"code": "518880", "name": "黄金ETF", "fund_type": "ETF", "invest_type": "商品型", "t_plus": "T+0"},
    # LOF
    {"code": "161725", "name": "招商中证白酒指数LOF", "fund_type": "LOF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "161005", "name": "富国天惠LOF", "fund_type": "LOF", "invest_type": "股票型", "t_plus": "T+1"},
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def sync_fund_list_with_fallback(db, source):
    """同步基金列表：优先用 spot API，失败则用种子代码回退"""
    try:
        funds = source.fetch_fund_list()
        if funds:
            db.upsert_fund_info(funds)
            logger.info(f"  通过 spot API 获取 {len(funds)} 只基金")
            return len(funds)
    except Exception as e:
        logger.warning(f"  spot API 失败: {e}，使用种子代码回退")

    # 回退：使用种子代码
    fallback = []
    for f in SEED_FUNDS:
        fallback.append({**f, "list_date": "", "is_excluded": 0})
    db.upsert_fund_info(fallback)
    logger.info(f"  使用种子代码回退: {len(fallback)} 只基金")
    return len(fallback)


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH

    logger.info("=" * 60)
    logger.info("FUNDFLOW 数据同步工具")
    logger.info("=" * 60)
    logger.info(f"数据库路径: {db_path}")

    # 确保数据库目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db = Database(db_path)
    db.init()

    source = AkshareSource()

    # 步骤 1: 同步基金列表（带回退）
    logger.info("-" * 40)
    logger.info("[1/3] 同步基金列表...")
    t0 = time.time()
    fund_count = sync_fund_list_with_fallback(db, source)
    logger.info(f"  完成: {fund_count} 只基金 (耗时 {time.time()-t0:.1f}s)")

    # 步骤 2: 同步日线行情（逐只报告进度）
    logger.info("-" * 40)
    logger.info("[2/3] 同步日线行情...")
    t0 = time.time()
    funds = db.get_all_active_funds()
    total_quotes = 0
    success_count = 0
    fail_count = 0
    for i, fund in enumerate(funds):
        code = fund["code"]
        name = fund["name"]
        try:
            quotes = source.fetch_daily_quotes(code)
            if quotes:
                for q in quotes:
                    q["code"] = code
                    q.setdefault("nav", None)
                    q.setdefault("premium_rate", None)
                    q.setdefault("prev_close", None)
                    q.setdefault("is_suspended", 0)
                    q.setdefault("suspended_days", 0)
                db.upsert_daily_quotes(quotes)
                total_quotes += len(quotes)
                success_count += 1
                logger.info(f"  [{i+1}/{len(funds)}] {code} {name}: {len(quotes)} 条")
            else:
                fail_count += 1
                logger.warning(f"  [{i+1}/{len(funds)}] {code} {name}: 无数据")
        except Exception as e:
            fail_count += 1
            logger.error(f"  [{i+1}/{len(funds)}] {code} {name}: 失败 - {e}")
    quotes_count = total_quotes
    logger.info(f"  完成: {quotes_count} 条行情记录 (成功 {success_count}/{len(funds)}, 失败 {fail_count}, 耗时 {time.time()-t0:.1f}s)")

    # 步骤 3: 同步净值
    logger.info("-" * 40)
    logger.info("[3/3] 同步基金净值...")
    t0 = time.time()
    pipeline = DataSyncPipeline(db, source)
    nav_count = pipeline.sync_nav_for_all()
    logger.info(f"  完成: {nav_count} 条净值记录 (耗时 {time.time()-t0:.1f}s)")

    db.close()

    # 汇总
    logger.info("=" * 60)
    logger.info("同步完成!")
    logger.info(f"  基金列表: {fund_count} 只")
    logger.info(f"  日线行情: {quotes_count} 条")
    logger.info(f"  净值记录: {nav_count} 条")
    logger.info(f"  数据库大小: {os.path.getsize(db_path) / 1024:.1f} KB")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""一键数据同步脚本：将项目目标基金的真实历史数据导入 SQLite。"""
import logging
import os
import sys
import time

import akshare as ak

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.models.database import Database
from engine.seed_sync import (
    PROJECT_TARGET_FUNDS,
    build_seed_fund_records,
    classify_exchange_symbol,
    normalize_nav_history,
    normalize_sina_daily_quotes,
)


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


def load_real_name_map() -> dict[str, str]:
    df = ak.fund_name_em()
    name_map = {}
    for _, row in df.iterrows():
        code = str(row["基金代码"]).zfill(6)
        name = str(row["基金简称"]).strip()
        if code and name:
            name_map[code] = name
    return name_map


def fetch_market_quotes(code: str) -> list[dict]:
    symbol = classify_exchange_symbol(code)
    df = ak.fund_etf_hist_sina(symbol=symbol)
    return normalize_sina_daily_quotes(code, df.to_dict("records"))


def fetch_nav_history(code: str) -> list[dict]:
    df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
    return normalize_nav_history(df.to_dict("records"))


def sync_project_target_funds(db: Database) -> tuple[int, int, int]:
    logger.info("[1/3] 读取真实基金名称总表...")
    t0 = time.time()
    name_map = load_real_name_map()
    fund_records = build_seed_fund_records(name_map)
    db.upsert_fund_info(fund_records)
    logger.info(f"  完成: {len(fund_records)} 只目标基金 (耗时 {time.time() - t0:.1f}s)")

    logger.info("[2/3] 拉取真实市场日线 OHLC...")
    t0 = time.time()
    quotes_total = 0
    quote_success = 0
    for index, fund in enumerate(fund_records, start=1):
        code = fund["code"]
        name = fund["name"]
        quotes = fetch_market_quotes(code)
        if not quotes:
            raise RuntimeError(f"{code} {name} 的市场日线为空，停止导入")
        db.upsert_daily_quotes(quotes)
        quotes_total += len(quotes)
        quote_success += 1
        logger.info(f"  [{index}/{len(fund_records)}] {code} {name}: {len(quotes)} 条市场日线")
    logger.info(
        f"  完成: {quotes_total} 条市场日线 (成功 {quote_success}/{len(fund_records)}, 耗时 {time.time() - t0:.1f}s)"
    )

    logger.info("[3/3] 拉取真实净值历史并回填...")
    t0 = time.time()
    nav_total = 0
    nav_success = 0
    for index, fund in enumerate(fund_records, start=1):
        code = fund["code"]
        name = fund["name"]
        nav_history = fetch_nav_history(code)
        if not nav_history:
            raise RuntimeError(f"{code} {name} 的净值历史为空，停止导入")
        for item in nav_history:
            db._update_nav(code, item["date"], item["nav"])
            nav_total += 1
        nav_success += 1
        logger.info(f"  [{index}/{len(fund_records)}] {code} {name}: {len(nav_history)} 条净值")
    logger.info(
        f"  完成: {nav_total} 条净值记录 (成功 {nav_success}/{len(fund_records)}, 耗时 {time.time() - t0:.1f}s)"
    )

    return len(fund_records), quotes_total, nav_total


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH

    logger.info("=" * 60)
    logger.info("FUNDFLOW 目标基金数据库初始化工具")
    logger.info("=" * 60)
    logger.info(f"数据库路径: {db_path}")
    logger.info(f"目标基金数: {len(PROJECT_TARGET_FUNDS)}")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db = Database(db_path)
    db.init()
    try:
        fund_count, quotes_count, nav_count = sync_project_target_funds(db)
    finally:
        db.close()

    logger.info("=" * 60)
    logger.info("初始化完成")
    logger.info(f"  基金列表: {fund_count} 只")
    logger.info(f"  市场日线: {quotes_count} 条")
    logger.info(f"  历史净值: {nav_count} 条")
    logger.info(f"  数据库大小: {os.path.getsize(db_path) / 1024:.1f} KB")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

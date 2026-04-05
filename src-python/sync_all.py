#!/usr/bin/env python3
"""一键数据同步脚本：初始化全量场内 ETF+LOF（排除货币/债券）数据库。"""
import logging
import os
import sys
import time

import akshare as ak

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.models.database import Database
from engine.seed_sync import (
    build_full_market_fund_records,
    classify_exchange_symbol,
    normalize_latest_nav_snapshots,
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


def load_name_rows() -> list[dict]:
    return ak.fund_name_em().to_dict("records")


def load_etf_rows() -> list[dict]:
    return ak.fund_etf_category_sina(symbol="ETF基金").to_dict("records")


def load_lof_rows() -> list[dict]:
    return ak.fund_etf_category_sina(symbol="LOF基金").to_dict("records")


def load_fallback_details() -> dict[str, dict]:
    # `501023` 在 fund_name_em 中缺失，但 overview 与净值/行情接口可用。
    return {
        "501023": {
            "name": "鹏华香港中小企业指数LOF",
            "fund_type_raw": "指数型-股票",
        }
    }


def fetch_market_quotes(code: str) -> list[dict]:
    symbol = classify_exchange_symbol(code)
    df = ak.fund_etf_hist_sina(symbol=symbol)
    return normalize_sina_daily_quotes(code, df.to_dict("records"))


def load_latest_nav_snapshots() -> dict[str, dict]:
    snapshots = {}
    snapshots.update(
        normalize_latest_nav_snapshots(
            ak.fund_etf_fund_daily_em().to_dict("records"),
            discount_key="折价率",
        )
    )
    snapshots.update(
        normalize_latest_nav_snapshots(
            ak.fund_open_fund_daily_em().to_dict("records"),
            discount_key=None,
        )
    )
    return snapshots


def sync_full_market_funds(db: Database) -> tuple[int, int, int, int]:
    logger.info("[1/3] 读取全量场内 ETF/LOF 清单并过滤货币/债券基金...")
    t0 = time.time()
    fund_records = build_full_market_fund_records(
        load_name_rows(),
        load_etf_rows(),
        load_lof_rows(),
        fallback_details=load_fallback_details(),
    )
    db.upsert_fund_info(fund_records)
    logger.info(f"  完成: {len(fund_records)} 只全量基金 (耗时 {time.time() - t0:.1f}s)")

    logger.info("[2/3] 拉取全量真实市场日线 OHLC...")
    t0 = time.time()
    quotes_total = 0
    skipped_no_market = 0
    for index, fund in enumerate(fund_records, start=1):
        code = fund["code"]
        name = fund["name"]
        if fund.get("has_market_data", 1) == 0:
            logger.info(f"  跳过 {code} {name}（无场内交易行情）")
            skipped_no_market += 1
            continue
        quotes = fetch_market_quotes(code)
        if not quotes:
            logger.warning(f"  警告: {code} {name} 有行情标记但返回空，更新为无行情")
            db.update_has_market_data(code, 0)
            skipped_no_market += 1
            continue
        db.upsert_daily_quotes(quotes)
        quotes_total += len(quotes)
        if index % 100 == 0 or index == len(fund_records):
            logger.info(f"  进度: {index}/{len(fund_records)}，累计 {quotes_total} 条市场日线")
    logger.info(f"  完成: {quotes_total} 条市场日线 (跳过 {skipped_no_market} 只无行情基金, 耗时 {time.time() - t0:.1f}s)")

    logger.info("[3/3] 回填全量最新净值快照...")
    t0 = time.time()
    latest_nav_snapshots = load_latest_nav_snapshots()
    nav_total = 0
    nav_covered = 0
    for index, fund in enumerate(fund_records, start=1):
        code = fund["code"]
        snapshot = latest_nav_snapshots.get(code)
        if snapshot is None:
            raise RuntimeError(f"{code} 缺少最新净值快照，停止导入")

        db.upsert_fund_nav_history([
            {"code": code, "date": snapshot["date"], "nav": snapshot["nav"]}
        ])
        db._update_nav(code, snapshot["date"], snapshot["nav"])
        nav_total += 1
        nav_covered += 1

        if snapshot.get("premium_rate") is not None:
            c = db.conn.cursor()
            c.execute(
                "UPDATE daily_quote SET premium_rate=? WHERE code=? AND date=?",
                (snapshot["premium_rate"], code, snapshot["date"]),
            )
            db.conn.commit()

        if index % 200 == 0 or index == len(fund_records):
            logger.info(f"  进度: {index}/{len(fund_records)}，累计 {nav_total} 条最新净值")

    logger.info(f"  完成: {nav_total} 条最新净值快照 (覆盖 {nav_covered}/{len(fund_records)}, 耗时 {time.time() - t0:.1f}s)")

    return len(fund_records), quotes_total, nav_total, skipped_no_market


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH

    logger.info("=" * 60)
    logger.info("FUNDFLOW 全量库初始化工具")
    logger.info("=" * 60)
    logger.info(f"数据库路径: {db_path}")
    logger.info("口径: 全量场内 ETF+LOF（排除货币/债券），内置全量历史日线 + 全量最新净值")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db = Database(db_path)
    db.init()
    try:
        fund_count, quotes_count, nav_count, skipped_count = sync_full_market_funds(db)
    finally:
        db.close()

    with_market = fund_count - skipped_count
    logger.info("=" * 60)
    logger.info("初始化完成")
    logger.info(f"  基金列表: {fund_count} 只（有行情: {with_market}, 无行情: {skipped_count}）")
    logger.info(f"  市场日线: {quotes_count} 条")
    logger.info(f"  最新净值: {nav_count} 条")
    logger.info(f"  数据库大小: {os.path.getsize(db_path) / 1024:.1f} KB")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

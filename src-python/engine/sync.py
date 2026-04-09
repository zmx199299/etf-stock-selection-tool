# src-python/engine/sync.py
"""数据同步管道：从 akshare 拉取数据写入 SQLite"""

import logging
from engine.models.database import Database
from engine.data.base import DataSource

logger = logging.getLogger(__name__)


class DataSyncPipeline:
    def __init__(self, db: Database, source: DataSource):
        self.db = db
        self.source = source

    def sync_fund_list(self) -> int:
        """同步基金列表到 fund_info 表"""
        funds = self.source.fetch_fund_list()
        self.db.upsert_fund_info(funds)
        logger.info(f"Synced {len(funds)} funds")
        return len(funds)

    def sync_daily_quotes_for_all(
        self, limit_days: int = None, max_consecutive_failures: int = 20
    ) -> int:
        """同步所有活跃且有行情数据的基金的日线行情到 daily_quote 表
        Args:
            limit_days: 限制抓取的天数，如果是 None 则抓取全部历史
            max_consecutive_failures: 连续失败多少只基金后提前终止同步，
                避免在所有数据源都不可用时浪费时间尝试全部基金
        """
        import datetime

        start_date = None
        if limit_days:
            start_date = (
                datetime.date.today() - datetime.timedelta(days=limit_days)
            ).isoformat()

        funds = self.db.get_all_funds_with_market_data()
        total = 0
        consecutive_failures = 0
        for fund in funds:
            code = fund["code"]
            quotes = self.source.fetch_daily_quotes(code, start_date=start_date)
            if not quotes:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    logger.warning(
                        f"连续 {consecutive_failures} 只基金无数据，"
                        f"提前终止日线同步（已处理 {total} 条行情）"
                    )
                    break
                continue
            # 有数据，重置连续失败计数
            consecutive_failures = 0
            for q in quotes:
                q["code"] = code
                # 提供默认值用于数据库插入
                q.setdefault("nav", None)
                q.setdefault("premium_rate", None)
                q.setdefault("prev_close", None)
                q.setdefault("is_suspended", 0)
                q.setdefault("suspended_days", 0)
            self.db.upsert_daily_quotes(quotes)
            total += len(quotes)
        logger.info(f"Synced {total} daily quotes for {len(funds)} funds")
        return total

    def sync_nav_for_all(self) -> int:
        """同步所有活跃且有行情数据的基金的净值到 daily_quote 表"""
        funds = self.db.get_all_funds_with_market_data()
        updated = 0
        for fund in funds:
            code = fund["code"]
            try:
                nav_data = self.source.fetch_nav(code)
                if not nav_data:
                    continue
                history_rows = []
                for nav_item in nav_data:
                    date = nav_item["date"]
                    nav = nav_item["nav"]
                    history_rows.append({"code": code, "date": date, "nav": nav})
                    self.db._update_nav(code, date, nav)
                    updated += 1
                self.db.upsert_fund_nav_history(history_rows)
            except Exception as e:
                logger.warning(f"同步基金 {code} 净值失败，跳过: {e}")
                continue
        logger.info(f"Updated nav for {updated} records")
        return updated

    def sync_minute_quotes_for_all(self, periods: list[str] = None) -> int:
        """同步所有基金的分钟线数据
        Args:
            periods: 需要同步的周期列表，默认 ['1', '5', '60']
        Returns:
            同步的总条数
        """
        if periods is None:
            periods = ["1", "5", "60"]

        funds = self.db.get_all_funds_with_market_data()
        total = 0

        for fund in funds:
            code = fund["code"]
            for period in periods:
                try:
                    quotes = self.source.fetch_minute_quotes(code, period)
                    if not quotes:
                        continue

                    # 添加 code 和 period 字段
                    for q in quotes:
                        q["code"] = code
                        q["period"] = period

                    self.db.upsert_minute_quotes(quotes)
                    total += len(quotes)
                except Exception as e:
                    logger.warning(f"Failed to sync {period}m quotes for {code}: {e}")
                    continue

        # 聚合 120 分钟线
        for fund in funds:
            try:
                quotes_120m = self.db.aggregate_120m_from_60m(fund["code"])
                if quotes_120m:
                    self.db.upsert_minute_quotes(quotes_120m)
                    total += len(quotes_120m)
            except Exception as e:
                logger.warning(f"Failed to aggregate 120m for {fund['code']}: {e}")
                continue

        logger.info(f"Synced {total} minute quotes for {len(funds)} funds")
        return total

    def sync_all(self, limit_days: int = None) -> dict:
        """执行完整同步流程
        Args:
            limit_days: 限制日线数据的天数，None 表示不限制（全部历史）
        """
        funds_count = self.sync_fund_list()
        quotes_count = self.sync_daily_quotes_for_all(limit_days=limit_days)
        nav_count = self.sync_nav_for_all()
        return {
            "funds_synced": funds_count,
            "quotes_synced": quotes_count,
            "nav_updated": nav_count,
        }

    def sync_fund_complete(self, code: str) -> dict:
        """为指定基金抓取完整的分钟线和日线数据
        用于技术分析页面按需加载

        Args:
            code: 基金代码
        Returns:
            抓取结果统计
        """
        logger.info(f"Fetching complete data for fund {code}...")

        # 1. 抓取分钟线数据（1分线5天 + 5分线 + 60分线）
        minute_counts = {}

        # 1分线：最近最近5天
        import datetime

        m1_start = (datetime.date.today() - datetime.timedelta(days=5)).isoformat()
        m1_quotes = self.source.fetch_minute_quotes(code, "1", start_date=m1_start)
        for q in m1_quotes:
            q["code"] = code
            q["period"] = "1"
        if m1_quotes:
            self.db.upsert_minute_quotes(m1_quotes)
        minute_counts["1m"] = len(m1_quotes)

        # 5分线：全部
        m5_quotes = self.source.fetch_minute_quotes(code, "5")
        for q in m5_quotes:
            q["code"] = code
            q["period"] = "5"
        if m5_quotes:
            self.db.upsert_minute_quotes(m5_quotes)
        minute_counts["5m"] = len(m5_quotes)

        # 60分线：全部
        m60_quotes = self.source.fetch_minute_quotes(code, "60")
        for q in m60_quotes:
            q["code"] = code
            q["period"] = "60"
        if m60_quotes:
            self.db.upsert_minute_quotes(m60_quotes)
        minute_counts["60m"] = len(m60_quotes)

        # 2. 抓取全部历史日线
        daily_quotes = self.source.fetch_daily_quotes(code)
        for q in daily_quotes:
            q["code"] = code
            q.setdefault("nav", None)
            q.setdefault("premium_rate", None)
            q.setdefault("prev_close", None)
            q.setdefault("is_suspended", 0)
            q.setdefault("suspended_days", 0)
        if daily_quotes:
            self.db.upsert_daily_quotes(daily_quotes)

        # 3. 抓取净值数据
        nav_data = self.source.fetch_nav(code)
        for nav_item in nav_data:
            date = nav_item["date"]
            nav = nav_item["nav"]
            self.db._update_nav(code, date, nav)

        logger.info(
            f"Complete data sync for {code}: {minute_counts}, {len(daily_quotes)} daily quotes"
        )
        return {
            "minute_counts": minute_counts,
            "daily_count": len(daily_quotes),
            "nav_count": len(nav_data),
        }

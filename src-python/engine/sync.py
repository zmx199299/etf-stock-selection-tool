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

    def sync_daily_quotes_for_all(self) -> int:
        """同步所有活跃且有行情数据的基金的日线行情到 daily_quote 表"""
        funds = self.db.get_all_funds_with_market_data()
        total = 0
        for fund in funds:
            code = fund["code"]
            quotes = self.source.fetch_daily_quotes(code)
            if not quotes:
                continue
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
            periods = ['1', '5', '60']

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

    def sync_all(self) -> dict:
        """执行完整同步流程"""
        funds_count = self.sync_fund_list()
        quotes_count = self.sync_daily_quotes_for_all()
        nav_count = self.sync_nav_for_all()
        return {
            "funds_synced": funds_count,
            "quotes_synced": quotes_count,
            "nav_updated": nav_count,
        }

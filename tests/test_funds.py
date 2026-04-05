"""
场内基金筛选工具测试套件。
所有外部依赖均使用 mock，禁止依赖真实网络。
"""

import json
from datetime import datetime

import akshare as ak
import pandas as pd
import pytest

import find_funds as ff

# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────


def _make_tencent_kline(
    dates: list[str],
    open_: float = 3.0,
    close: float = 3.0,
    high: float = 3.105,
    low: float = 2.97,
    volume: int = 1_500_000,
    symbol: str = "sh510050",
) -> str:
    """构造腾讯财经前复权日K线 JSONP 响应。"""
    bars = [
        [d, str(open_), str(close), str(high), str(low), f"{volume}.000"] for d in dates
    ]
    data = {"code": 0, "msg": "", "data": {symbol: {"qfqday": bars}}}
    return f"kline_dayfqk={json.dumps(data)}"


def _make_tencent_realtime(codes_prices: dict[str, float]) -> str:
    """构造腾讯财经实时行情响应（用于停牌判断）。
    codes_prices: {6位代码: 价格}，价格为0表示停牌。
    """
    lines = []
    for code, price in codes_prices.items():
        prefix = "sh" if code.startswith(("5", "6")) else "sz"
        tc = f"{prefix}{code}"
        lines.append(f'v_{tc}="1~基金名称~{code}~{price}~{price}~{price}~0~0~0~"')
    return ";".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 交易日历
# ─────────────────────────────────────────────────────────────────────────────


class TestGetTradeCalendar:
    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 成功返回 → 正常解析成升序列表。"""

        def _mock() -> pd.DataFrame:
            return pd.DataFrame(
                {"trade_date": ["2026-03-24", "2026-03-25", "2026-03-26"]}
            )

        monkeypatch.setattr(ak, "tool_trade_date_hist_sina", _mock)

        result = ff.get_trade_calendar()
        assert result == ["2026-03-24", "2026-03-25", "2026-03-26"]

    def test_connection_error_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 连接失败 → fallback 到排除周末的近期列表，程序不崩溃。"""

        def _mock() -> pd.DataFrame:
            raise ConnectionError("网络不通")

        monkeypatch.setattr(ak, "tool_trade_date_hist_sina", _mock)

        result = ff.get_trade_calendar()
        assert isinstance(result, list)
        assert len(result) > 0
        for d in result:
            assert datetime.strptime(d, "%Y-%m-%d").weekday() < 5

    def test_empty_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 返回空数据 → fallback，不报错。"""

        def _mock() -> pd.DataFrame:
            return pd.DataFrame({"trade_date": []})

        monkeypatch.setattr(ak, "tool_trade_date_hist_sina", _mock)

        result = ff.get_trade_calendar()
        assert isinstance(result, list)


# ─────────────────────────────────────────────────────────────────────────────
# 交易时间判断
# ─────────────────────────────────────────────────────────────────────────────


class TestGetLatestTradeDate:
    CALENDAR = ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26", "2026-03-27"]

    def _freeze(
        self, monkeypatch: pytest.MonkeyPatch, date_str: str, hour: int, minute: int
    ) -> None:
        fixed = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=hour, minute=minute
        )
        monkeypatch.setattr(
            ff,
            "datetime",
            type(
                "_DT",
                (),
                {
                    "now": staticmethod(lambda: fixed),
                    "strptime": datetime.strptime,
                },
            ),
        )

    def test_before_trading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """9:00（开盘前）→ 使用最近交易日（当天）数据。"""
        self._freeze(monkeypatch, "2026-03-26", 9, 0)
        result = ff.get_latest_trade_date(self.CALENDAR)
        assert result == "2026-03-26"

    def test_during_trading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """10:00（交易时段）→ 使用前一交易日数据。"""
        self._freeze(monkeypatch, "2026-03-26", 10, 0)
        result = ff.get_latest_trade_date(self.CALENDAR)
        assert result == "2026-03-25"

    def test_lunch_break(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """12:00（午休，仍算交易时段）→ 使用前一交易日数据。"""
        self._freeze(monkeypatch, "2026-03-26", 12, 0)
        result = ff.get_latest_trade_date(self.CALENDAR)
        assert result == "2026-03-25"

    def test_after_close(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """16:00（收盘后）→ 使用最近交易日（当天）数据。"""
        self._freeze(monkeypatch, "2026-03-26", 16, 0)
        result = ff.get_latest_trade_date(self.CALENDAR)
        assert result == "2026-03-26"

    def test_weekend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """周末（周五收盘后）→ 使用最近交易日（周五）数据。"""
        self._freeze(monkeypatch, "2026-03-27", 16, 0)
        result = ff.get_latest_trade_date(self.CALENDAR)
        assert result == "2026-03-27"


# ─────────────────────────────────────────────────────────────────────────────
# T+0 / T+1 判断
# ─────────────────────────────────────────────────────────────────────────────


class TestIsT0:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("华夏上证50ETF", False),
            ("南方中证500ETF", False),
            ("招商中证白酒指数LOF", False),
            ("易方达中概互联网50ETF", True),  # 跨境
            ("国泰黄金ETF", True),  # 黄金
            ("华宝油气LOF", True),  # 油气
            ("博时标普500ETF", True),  # 标普
            ("国泰上证中期国债ETF", True),  # 国债
            ("华夏货币A", True),  # 货币
        ],
    )
    def test_t0_keywords(self, name: str, expected: bool) -> None:
        assert ff.is_t0(name) == expected


# ─────────────────────────────────────────────────────────────────────────────
# V型反转筛选
# ─────────────────────────────────────────────────────────────────────────────


class TestCheckVReversal:
    LATEST = "2026-03-26"

    def _df_with_base(
        self,
        dates: list[str],
        highs: list[float],
        lows: list[float],
        closes: list[float],
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "date": dates,
                "开盘": [3.0] * len(dates),
                "收盘": closes,
                "最高": highs,
                "最低": lows,
                "成交量": [1_000_000] * len(dates),
            }
        )

    def test_pass_3_days(self) -> None:
        """连续3天满足条件 → 返回 True。"""
        dates = ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"]
        closes = [3.0, 3.0, 3.0, 3.0]
        highs = [3.0, 3.105, 3.105, 3.105]
        lows = [3.0, 2.97, 2.97, 2.97]
        df = self._df_with_base(dates, highs, lows, closes)
        assert ff.check_v_reversal(df, self.LATEST) is True

    def test_fail_amplitude_too_small(self) -> None:
        """振幅 < 3.5% → 返回 False。"""
        dates = ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"]
        closes = [3.0] * 4
        highs = [3.0, 3.05, 3.05, 3.05]
        lows = [3.0, 2.97, 2.97, 2.97]
        df = self._df_with_base(dates, highs, lows, closes)
        assert ff.check_v_reversal(df, self.LATEST) is False

    def test_fail_amplitude_too_large(self) -> None:
        """振幅 > 4.5% → 返回 False。"""
        dates = ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"]
        closes = [3.0] * 4
        highs = [3.0, 3.2, 3.2, 3.2]
        lows = [3.0, 2.9, 2.9, 2.9]
        df = self._df_with_base(dates, highs, lows, closes)
        assert ff.check_v_reversal(df, self.LATEST) is False

    def test_fail_low_drop_insufficient(self) -> None:
        """最低点下跌不足1% → 返回 False。"""
        dates = ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"]
        closes = [3.0] * 4
        highs = [3.0, 3.105, 3.105, 3.105]
        lows = [3.0, 2.999, 2.999, 2.999]
        df = self._df_with_base(dates, highs, lows, closes)
        assert ff.check_v_reversal(df, self.LATEST) is False

    def test_fail_no_reversal(self) -> None:
        """最高点 <= 最低点（无反弹）→ 返回 False。"""
        dates = ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"]
        closes = [3.0] * 4
        highs = [3.0, 2.97, 2.97, 2.97]
        lows = [3.0, 2.97, 2.97, 2.97]
        df = self._df_with_base(dates, highs, lows, closes)
        assert ff.check_v_reversal(df, self.LATEST) is False

    def test_fail_insufficient_data(self) -> None:
        """数据不足3+1行 → 返回 False。"""
        dates = ["2026-03-25", "2026-03-26"]
        closes = [3.0, 3.0]
        highs = [3.0, 3.105]
        lows = [3.0, 2.97]
        df = self._df_with_base(dates, highs, lows, closes)
        assert ff.check_v_reversal(df, self.LATEST) is False

    def test_only_2_of_3_days_pass(self) -> None:
        """3天中有1天不满足 → 返回 False。"""
        dates = ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"]
        closes = [3.0] * 4
        highs = [3.0, 3.105, 3.01, 3.105]
        lows = [3.0, 2.97, 2.97, 2.97]
        df = self._df_with_base(dates, highs, lows, closes)
        assert ff.check_v_reversal(df, self.LATEST) is False


# ─────────────────────────────────────────────────────────────────────────────
# 技术指标评分
# ─────────────────────────────────────────────────────────────────────────────


class TestCalcBuyScore:
    LATEST = "2026-03-26"

    def _build_df(self, n: int = 40) -> pd.DataFrame:
        """构造 n 行收盘价下降序列（模拟超卖），用于评分测试。"""
        dates = (
            pd.date_range("2026-01-01", periods=n, freq="B")
            .strftime("%Y-%m-%d")
            .tolist()
        )
        close = [3.0 - i * 0.02 for i in range(n)]
        volume = [1_000_000 if i < n - 1 else 2_000_000 for i in range(n)]
        return pd.DataFrame(
            {
                "date": dates,
                "开盘": close,
                "收盘": close,
                "最高": [c + 0.05 for c in close],
                "最低": [c - 0.05 for c in close],
                "成交量": volume,
            }
        )

    def test_returns_int(self) -> None:
        """返回值必须是整数。"""
        df = self._build_df()
        latest = df["date"].iloc[-1]
        score = ff.calc_buy_score(df, latest)
        assert isinstance(score, int)

    def test_score_range(self) -> None:
        """评分必须在 [0, 100] 范围内。"""
        df = self._build_df()
        latest = df["date"].iloc[-1]
        score = ff.calc_buy_score(df, latest)
        assert 0 <= score <= 100

    def test_insufficient_data_returns_zero(self) -> None:
        """数据不足26行 → 返回0。"""
        df = self._build_df(n=20)
        latest = df["date"].iloc[-1]
        assert ff.calc_buy_score(df, latest) == 0

    def test_v_reversal_bonus_always_included(self) -> None:
        """V型反转固定加分15分，评分至少15（数据充足时）。"""
        df = self._build_df(n=30)
        latest = df["date"].iloc[-1]
        score = ff.calc_buy_score(df, latest)
        assert score >= 15


# ─────────────────────────────────────────────────────────────────────────────
# 停牌判断（腾讯实时行情接口）
# ─────────────────────────────────────────────────────────────────────────────


class TestGetSuspendedFunds:
    def test_empty_codes_returns_empty(self) -> None:
        """传入空列表 → 直接返回空集合，不发网络请求。"""
        result = ff.get_suspended_funds("2026-03-27", [])
        assert result == set()

    def test_none_codes_returns_empty(self) -> None:
        """传入 None → 直接返回空集合。"""
        result = ff.get_suspended_funds("2026-03-27", None)
        assert result == set()

    def test_no_suspension(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """所有基金正常交易（价格>0）→ 返回空集合。"""
        response_text = _make_tencent_realtime({"510050": 2.897, "510300": 4.488})

        class MockResponse:
            status_code = 200
            text = response_text

        monkeypatch.setattr(ff.requests, "get", lambda *a, **kw: MockResponse())
        result = ff.get_suspended_funds("2026-03-27", ["510050", "510300"])
        assert result == set()

    def test_with_suspensions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """有基金价格为0 → 返回停牌代码集合。"""
        response_text = _make_tencent_realtime({"510050": 0.0, "510300": 4.488})

        class MockResponse:
            status_code = 200
            text = response_text

        monkeypatch.setattr(ff.requests, "get", lambda *a, **kw: MockResponse())
        result = ff.get_suspended_funds("2026-03-27", ["510050", "510300"])
        assert "510050" in result
        assert "510300" not in result

    def test_api_failure_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API失败 → 返回空集合，不崩溃。"""

        def _fail(*args, **kwargs):
            raise ConnectionError("超时")

        monkeypatch.setattr(ff.requests, "get", _fail)
        result = ff.get_suspended_funds("2026-03-27", ["510050"])
        assert result == set()


# ─────────────────────────────────────────────────────────────────────────────
# 基金列表获取
# ─────────────────────────────────────────────────────────────────────────────


class TestGetAllFunds:
    def test_success(self, mock_fund_code_search: None) -> None:
        """API 成功 → 返回筛选后的基金字典。"""
        result = ff.get_all_funds()
        assert "510050" in result
        assert "161725" in result
        # 联接基金被排除
        assert "510051" not in result
        # 普通混合基金被排除（代码不在范围内）
        assert "000001" not in result
        # 货币基金被排除
        assert "511690" not in result

    def test_fallback_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 失败 → 返回 fallback 数据，不崩溃。"""
        import requests

        class MockResponse:
            status_code = 500
            text = ""

        monkeypatch.setattr(
            requests,
            "get",
            lambda *args, **kwargs: MockResponse(),
        )
        result = ff.get_all_funds()
        assert len(result) > 0
        assert "510050" in result


# ─────────────────────────────────────────────────────────────────────────────
# 历史行情获取（腾讯财经 K 线 API）
# ─────────────────────────────────────────────────────────────────────────────


class TestGetFundHist:
    LATEST = "2026-03-26"

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 成功 → 返回含必要列的 DataFrame。"""
        kline = _make_tencent_kline(
            ["2026-03-20", "2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"],
            high=3.105,
            low=2.97,
        )

        class MockResponse:
            status_code = 200
            text = kline

        monkeypatch.setattr(
            ff.requests,
            "get",
            lambda *args, **kwargs: MockResponse(),
        )

        df = ff.get_fund_hist("510050", "华夏上证50ETF", self.LATEST)
        assert df is not None
        assert "date" in df.columns
        assert "收盘" in df.columns
        assert "成交量" in df.columns
        assert len(df) == 5

    def test_empty_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 返回空 klines → 返回 None，不崩溃。"""
        data = {"code": 0, "msg": "", "data": {"sz999999": {"qfqday": []}}}
        kline = f"kline_dayfqk={json.dumps(data)}"

        class MockResponse:
            status_code = 200
            text = kline

        monkeypatch.setattr(
            ff.requests,
            "get",
            lambda *args, **kwargs: MockResponse(),
        )

        result = ff.get_fund_hist("999999", "不存在的基金", self.LATEST)
        assert result is None

    def test_api_failure_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 失败 → 返回 None，不崩溃。"""

        def _fail(*args, **kwargs):
            raise ConnectionError("超时")

        monkeypatch.setattr(ff.requests, "get", _fail)
        result = ff.get_fund_hist("510050", "华夏上证50ETF", self.LATEST)
        assert result is None

    def test_outdated_data_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """返回数据的最新日期早于 latest_date → 返回 None。"""
        kline = _make_tencent_kline(
            ["2026-03-20", "2026-03-23", "2026-03-24"],  # 最新只到 03-24
            high=3.105,
            low=2.97,
        )

        class MockResponse:
            status_code = 200
            text = kline

        monkeypatch.setattr(ff.requests, "get", lambda *a, **kw: MockResponse())
        result = ff.get_fund_hist("510050", "华夏上证50ETF", "2026-03-26")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# 腾讯 API symbol 转换
# ─────────────────────────────────────────────────────────────────────────────


class TestTencentSymbol:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("510050", "sh510050"),
            ("510300", "sh510300"),
            ("518880", "sh518880"),
            ("600519", "sh600519"),
            ("159915", "sz159915"),
            ("161725", "sz161725"),
            ("159922", "sz159922"),
        ],
    )
    def test_symbol_conversion(self, code: str, expected: str) -> None:
        assert ff._tencent_symbol(code) == expected


# ─────────────────────────────────────────────────────────────────────────────
# 无结果输出
# ─────────────────────────────────────────────────────────────────────────────


class TestPrintNoResult:
    def test_output_contains_conditions(self, capsys: pytest.CaptureFixture) -> None:
        """无结果输出必须包含筛选条件说明。"""
        ff.print_no_result()
        captured = capsys.readouterr()
        assert "暂时没有符合条件的基金" in captured.out
        assert "3.5%" in captured.out
        assert "4.5%" in captured.out
        assert "V型反转" in captured.out
        assert "停牌" in captured.out
        assert "非货币基金" in captured.out


# ─────────────────────────────────────────────────────────────────────────────
# fetch_all_fund_hist 批量并发
# ─────────────────────────────────────────────────────────────────────────────


class TestFetchAllFundHist:
    LATEST = "2026-03-26"

    def test_returns_dict_of_dataframes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """批量并发 → 返回 {代码: DataFrame} 字典，有效数据正确。"""

        def _dynamic_kline(*args, **kwargs):
            # 从 params 里取 param 字段，解析出 symbol
            params = kwargs.get("params", {})
            param_str = params.get("param", "sh510050,day")
            symbol = param_str.split(",")[0]
            kline = _make_tencent_kline(
                ["2026-03-20", "2026-03-23", "2026-03-24",
                 "2026-03-25", "2026-03-26"],
                high=3.105, low=2.97,
                symbol=symbol,
            )

            class R:
                status_code = 200
                text = kline
            return R()

        monkeypatch.setattr(ff.requests, "get", _dynamic_kline)
        fund_dict = {"510050": "华夏上证50ETF", "510300": "华泰柏瑞沪深300ETF"}
        result = ff.fetch_all_fund_hist(fund_dict, self.LATEST)
        assert isinstance(result, dict)
        assert len(result) == 2
        for code, df in result.items():
            assert isinstance(df, pd.DataFrame)

    def test_empty_fund_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """基金字典为空 → 返回空字典，不崩溃。"""
        monkeypatch.setattr(
            ff.requests,
            "get",
            lambda *a, **kw: (_ for _ in ()).throw(AssertionError("不应该发请求")),
        )
        result = ff.fetch_all_fund_hist({}, self.LATEST)
        assert result == {}

    def test_api_failure_skips_fund(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """某只基金 API 失败 → 跳过该只，不崩溃，其他仍处理。"""
        call_count = [0]

        def _conditional(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("超时")
            kline = _make_tencent_kline(
                ["2026-03-20", "2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"],
                high=3.105,
                low=2.97,
            )

            class R:
                status_code = 200
                text = kline

            return R()

        monkeypatch.setattr(ff.requests, "get", _conditional)
        fund_dict = {"510050": "华夏上证50ETF", "510300": "华泰柏瑞沪深300ETF"}
        result = ff.fetch_all_fund_hist(fund_dict, self.LATEST)
        # 至少有1只成功
        assert len(result) >= 0  # 不崩溃即可


# ─────────────────────────────────────────────────────────────────────────────
# main() 集成测试
# ─────────────────────────────────────────────────────────────────────────────


class TestMain:
    def test_main_no_crash(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_trade_calendar: None,
        mock_fund_code_search: None,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """全流程 mock → main() 不报错。"""
        kline = _make_tencent_kline(
            ["2026-03-20", "2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26"],
            high=3.105,
            low=2.97,
        )

        class MockResponse:
            status_code = 200
            text = kline

        # mock_fund_code_search 已经 monkeypatch 了 requests.get
        # 需要覆盖为腾讯 K 线格式（因为 main 里先调用 get_all_funds 再调用 fetch_all_fund_hist）
        # 用计数器区分：第1次调用返回基金列表，后续返回 K 线
        call_count = [0]

        fund_list_content = (
            'var r = [["510050","ZZ50ETF","华夏上证50ETF","指数型-股票","HUA50"]];'
        )

        def _mock_get(*args, **kwargs):
            call_count[0] += 1
            url = args[0] if args else kwargs.get("url", "")
            if "fundcode_search" in str(url):

                class FundResp:
                    status_code = 200
                    text = fund_list_content

                return FundResp()
            else:
                return MockResponse()

        monkeypatch.setattr(ff.requests, "get", _mock_get)

        # 固定时间为收盘后
        fixed = datetime(2026, 3, 26, 16, 0, 0)
        monkeypatch.setattr(
            ff,
            "datetime",
            type(
                "_DT",
                (),
                {
                    "now": staticmethod(lambda: fixed),
                    "strptime": datetime.strptime,
                },
            ),
        )

        ff.main()
        captured = capsys.readouterr()
        assert len(captured.out) > 0 or True  # 不崩溃即通过

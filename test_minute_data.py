#!/usr/bin/env python3
"""测试akshare分钟线数据获取能力"""
import akshare as ak
import pandas as pd
import time
import sys

def test_etf_minute():
    """测试ETF分钟线数据"""
    print("测试ETF分钟线数据...")
    test_codes = ['510300', '159915', '510500']  # 沪深300ETF, 创业板ETF, 中证500ETF
    
    for code in test_codes:
        print(f"\n--- 测试 {code} ---")
        for period in ['1', '5', '60']:
            try:
                print(f"  获取 {period}分钟线...", end='')
                df = ak.fund_etf_hist_min_em(symbol=code, period=period)
                print(f" 成功，形状: {df.shape}")
                
                if not df.empty:
                    print(f"    列名: {list(df.columns)}")
                    print(f"    时间范围: {df.iloc[0]['时间'] if '时间' in df.columns else 'N/A'} 到 {df.iloc[-1]['时间'] if '时间' in df.columns else 'N/A'}")
                    
                    # 统计天数
                    if '时间' in df.columns:
                        df['日期'] = df['时间'].str.split(' ').str[0]
                        days = df['日期'].nunique()
                        print(f"    包含天数: {days}天")
                        
                        if days > 0:
                            # 显示日期范围
                            dates = sorted(df['日期'].unique())
                            print(f"    日期范围: {dates[0]} 到 {dates[-1]}")
                
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                print(f" 失败: {e}")
                continue

def test_lof_minute():
    """测试LOF分钟线数据"""
    print("\n\n测试LOF分钟线数据...")
    test_codes = ['162411', '161725']  # 华宝油气, 招商白酒
    
    for code in test_codes:
        print(f"\n--- 测试 {code} ---")
        for period in ['1', '5', '60']:
            try:
                print(f"  获取 {period}分钟线...", end='')
                df = ak.fund_lof_hist_min_em(symbol=code, period=period)
                print(f" 成功，形状: {df.shape}")
                
                if not df.empty:
                    print(f"    列名: {list(df.columns)}")
                    if '时间' in df.columns:
                        print(f"    时间范围: {df.iloc[0]['时间']} 到 {df.iloc[-1]['时间']}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f" 失败: {e}")
                continue

def test_daily_data_for_comparison():
    """测试日线数据作为对比"""
    print("\n\n测试日线数据作为对比...")
    code = '510300'
    
    try:
        print(f"获取 {code} 日线数据...")
        df = ak.fund_etf_hist_em(symbol=code, period='daily')
        print(f"日线形状: {df.shape}")
        
        if not df.empty and '日期' in df.columns:
            print(f"日线日期范围: {df.iloc[0]['日期']} 到 {df.iloc[-1]['日期']}")
            days = df['日期'].nunique()
            print(f"日线包含天数: {days}天")
            
    except Exception as e:
        print(f"日线获取失败: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("akshare分钟线数据能力测试")
    print("=" * 60)
    
    try:
        test_etf_minute()
        test_lof_minute()
        test_daily_data_for_comparison()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
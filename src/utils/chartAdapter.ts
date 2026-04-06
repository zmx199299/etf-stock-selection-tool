export function buildIntradayOption(periodData: any, colorMode: 'cn' | 'intl'): any {
  if (!periodData || !periodData.timeAxis) return {}
  const lineCol = colorMode === 'cn' ? '#ef4444' : '#16a34a'
  const avgCol = colorMode === 'cn' ? '#22c55e' : '#ef4444'
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: '10%', right: '5%', top: '5%', height: '60%' }, { left: '10%', right: '5%', top: '75%', height: '20%' }],
    xAxis: [
      { type: 'category', data: periodData.timeAxis, gridIndex: 0, boundaryGap: false },
      { type: 'category', data: periodData.timeAxis, gridIndex: 1, boundaryGap: false, show: false }
    ],
    yAxis: [{ type: 'value', scale: true, gridIndex: 0 }, { type: 'value', gridIndex: 1 }],
    series: [
      { name: '价格', type: 'line', data: periodData.linePoints, xAxisIndex: 0, yAxisIndex: 0, lineStyle: { color: lineCol }, showSymbol: false },
      { name: '均价', type: 'line', data: periodData.avgLinePoints, xAxisIndex: 0, yAxisIndex: 0, lineStyle: { color: avgCol, type: 'dashed' }, showSymbol: false },
      { name: '成交量', type: 'bar', data: periodData.volumes, xAxisIndex: 1, yAxisIndex: 1 }
    ]
  }
}

export function buildKLineOption(periodData: any, colorMode: 'cn' | 'intl'): any {
  if (!periodData || !periodData.timeAxis) return {}
  const upColor = colorMode === 'cn' ? '#ef4444' : '#22c55e'
  const downColor = colorMode === 'cn' ? '#22c55e' : '#ef4444'
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: '10%', right: '5%', top: '5%', height: '60%' }, { left: '10%', right: '5%', top: '75%', height: '20%' }],
    xAxis: [
      { type: 'category', data: periodData.timeAxis, gridIndex: 0 },
      { type: 'category', data: periodData.timeAxis, gridIndex: 1, show: false }
    ],
    yAxis: [{ type: 'value', scale: true, gridIndex: 0 }, { type: 'value', gridIndex: 1 }],
    series: [
      { name: 'K线', type: 'candlestick', data: periodData.candles, itemStyle: { color: upColor, color0: downColor, borderColor: upColor, borderColor0: downColor }, xAxisIndex: 0, yAxisIndex: 0 },
      { name: '成交量', type: 'bar', data: periodData.volumes, xAxisIndex: 1, yAxisIndex: 1 }
    ]
  }
}

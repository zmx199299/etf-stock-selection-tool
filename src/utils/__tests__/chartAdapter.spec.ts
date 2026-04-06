import { describe, it, expect } from 'vitest'
import { buildIntradayOption } from '../chartAdapter'

describe('chartAdapter', () => {
  it('buildIntradayOption builds correct option', () => {
    const periodData = { timeAxis: ['09:30', '09:31'], linePoints: [1.0, 1.1], avgLinePoints: [1.0, 1.05], volumes: [100, 200] }
    const option = buildIntradayOption(periodData as any, 'cn')
    expect(option.series).toHaveLength(3) // price, avg, volume
    expect(option.xAxis[0].data).toEqual(['09:30', '09:31'])
  })
})

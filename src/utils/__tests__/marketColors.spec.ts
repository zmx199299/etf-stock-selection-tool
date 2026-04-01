import { describe, expect, it } from 'vitest'
import {
  getDirectionPalette,
  numericToDirection,
  scoreToDirection,
} from '../marketColors'

describe('marketColors', () => {
  it('按配色模式返回上涨颜色类名', () => {
    expect(getDirectionPalette('cn', 'bullish').valueClass).toBe('text-red-500')
    expect(getDirectionPalette('intl', 'bullish').valueClass).toBe('text-green-600')
  })

  it('返回收敛后的调色板字段集合', () => {
    expect(getDirectionPalette('cn', 'bullish')).toEqual({
      valueClass: 'text-red-500',
      softTextClass: 'text-red-400',
      dotClass: 'bg-red-500',
      barClass: 'bg-red-500',
    })
  })

  it('numericToDirection() 依据数值返回方向', () => {
    expect(numericToDirection(1.2)).toBe('bullish')
    expect(numericToDirection(0)).toBe('neutral')
    expect(numericToDirection(-1.2)).toBe('bearish')
  })

  it('scoreToDirection() 依据评分返回方向', () => {
    expect(scoreToDirection(9)).toBe('bullish')
    expect(scoreToDirection(5)).toBe('neutral')
    expect(scoreToDirection(2)).toBe('bearish')
  })
})

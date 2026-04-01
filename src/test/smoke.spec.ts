import { describe, expect, it } from 'vitest'

describe('前端测试基线', () => {
  it('可以读写 localStorage', () => {
    localStorage.setItem('smoke-key', 'smoke-value')

    expect(localStorage.getItem('smoke-key')).toBe('smoke-value')
  })
})

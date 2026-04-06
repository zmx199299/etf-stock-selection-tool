import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Scoring from '../Scoring.vue'

// Mock tauri invoke
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn()
}))

describe('Scoring.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially and then real data', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    const mockInvoke = invoke as any
    
    mockInvoke.mockResolvedValue({
      code: '510300',
      name: '测试ETF',
      price: 1.0,
      change: 2.0,
      trend_score: 80,
      momentum_score: 80,
      volatility_score: 80,
      volume_score: 80,
      total_score: 80,
      signal: '看多',
      advice_amount: 1000,
      estimate_fee: 1.5,
      stop_loss: 0.9,
      take_profit: 1.1
    })

    const wrapper = mount(Scoring)
    
    // Check loading text
    expect(wrapper.text()).toContain('加载中')
    
    // Wait for promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0))
    await wrapper.vm.$nextTick()
    
    // Check data
    expect(wrapper.text()).toContain('测试ETF')
    expect(wrapper.text()).toContain('80')
    expect(wrapper.text()).toContain('1000 份')
    expect(mockInvoke).toHaveBeenCalledWith('invoke_engine', {
      method: 'get_scoring_data',
      params: { code: '510300' }
    })
  })
})
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import Analysis from '../Analysis.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { code: '510300' } }),
  useRouter: () => ({ push: vi.fn() })
}))

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn()
}))

describe('Analysis.vue real data', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('calls invoke_engine to fetch analysis data', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    const mockInvoke = invoke as any
    mockInvoke.mockResolvedValue({
      code: '510300',
      name: '测试ETF',
      price: '4.00',
      change: '1.0%',
      market: 'SH',
      iopv: '4.00',
      premium: '0.0%',
      riskLevel: '低风险',
      strategy: { conclusion: '观望' },
      periods: {
        day: { label: '日K', summary: 'test', chartSummary: 'test', metrics: [] }
      }
    })

    const wrapper = mount(Analysis, { 
      global: { 
        mocks: { $route: { query: { code: '510300' } } },
        stubs: ['v-chart'] 
      } 
    })
    
    // wait for promises
    await new Promise(r => setTimeout(r, 0))
    
    expect(mockInvoke).toHaveBeenCalledWith('invoke_engine', { method: 'get_analysis_data', params: { code: '510300' } })
    expect(wrapper.text()).toContain('测试ETF')
  })
})

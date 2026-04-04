import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import FundList from '../FundList.vue'
import { COLOR_MODE_STORAGE_KEY, useColorModeStore } from '../../stores/colorMode'

const pushMock = vi.fn()
const openMock = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

describe('FundList', () => {
  beforeEach(() => {
    localStorage.clear()
    pushMock.mockReset()
    openMock.mockReset()
    setActivePinia(createPinia())
    vi.stubGlobal('open', openMock)
  })

  it('搜索创业板后只显示匹配基金', async () => {
    const wrapper = mount(FundList)

    const searchInput = wrapper.get('[data-test="fund-search"]')
    await searchInput.setValue('创业板')

    expect(wrapper.text()).toContain('创业板ETF')
    expect(wrapper.text()).not.toContain('沪深300ETF')
  })

  it('大屏容器不会被固定最大宽度限制', () => {
    const wrapper = mount(FundList)
    const shell = wrapper.get('section > div')

    expect(shell.classes()).not.toContain('max-w-7xl')
    expect(shell.classes()).toContain('w-full')
  })

  it('顶部文案使用全量监测口径', () => {
    const wrapper = mount(FundList)

    expect(wrapper.text()).toContain('全量场内基金（不含货币/债券基金）')
    expect(wrapper.text()).toContain('共监测4支')
    expect(wrapper.text()).not.toContain('场内基金宽表')
    expect(wrapper.text()).not.toContain('支持代码和名称搜索')
  })

  it('第二页顶部栏采用固定框架，右侧控制区宽度固定为统一基线', () => {
    const wrapper = mount(FundList)

    expect(wrapper.get('[data-test="fund-shell"]').classes()).toEqual(
      expect.arrayContaining(['min-h-full', 'bg-slate-50', 'p-4', 'md:p-6']),
    )
    expect(wrapper.get('[data-test="fund-topbar"]').classes()).toEqual(
      expect.arrayContaining(['rounded-2xl', 'border', 'border-slate-200', 'bg-white', 'p-4', 'md:p-5']),
    )
    expect(wrapper.get('[data-test="fund-topbar-flex"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-4', 'lg:flex-row', 'lg:items-center', 'lg:justify-between']),
    )
    expect(wrapper.get('[data-test="fund-topbar-left"]').classes()).toEqual(
      expect.arrayContaining(['space-y-1']),
    )
    expect(wrapper.get('[data-test="fund-topbar-right"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-3', 'md:flex-row', 'md:items-center', 'lg:w-[380px]', 'lg:flex-none']),
    )
    expect(wrapper.get('[data-test="fund-tab-group"]').classes()).toEqual(
      expect.arrayContaining(['inline-flex', 'rounded-xl', 'bg-slate-100', 'p-1']),
    )
  })

  it('切换到 intl 模式会同步更新 store 和 localStorage', async () => {
    const wrapper = mount(FundList)
    const colorModeStore = useColorModeStore()

    await wrapper.get('[data-test="mode-intl"]').trigger('click')

    expect(colorModeStore.mode).toBe('intl')
    expect(localStorage.getItem(COLOR_MODE_STORAGE_KEY)).toBe('intl')
  })

  it('波动率按后端比率数据转换为百分比显示，并随共享颜色模式切换上涨语义类名', async () => {
    const wrapper = mount(FundList)
    const changeCell = wrapper.get('[data-test="change-510300"]')

    expect(wrapper.text()).toContain('1.72%')
    expect(changeCell.classes()).toContain('text-red-500')

    await wrapper.get('[data-test="mode-intl"]').trigger('click')

    expect(wrapper.get('[data-test="change-510300"]').classes()).toContain('text-green-600')
  })

  it('点击代码名称区域会打开雪球详情页', async () => {
    const wrapper = mount(FundList)

    await wrapper.get('[data-test="xueqiu-510300"]').trigger('click')

    expect(openMock).toHaveBeenCalledWith('https://xueqiu.com/S/SH510300', '_blank', 'noopener,noreferrer')
  })

  it('点击详情分析会跳转到 analysis 路由', async () => {
    const wrapper = mount(FundList)

    await wrapper.get('[data-test="detail-510300"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'analysis',
      query: { code: '510300' },
    })
  })

  it('详情分析跳转会携带 code 查询参数，供第三页直接进入详情态', async () => {
    const wrapper = mount(FundList)

    await wrapper.get('[data-test="detail-159915"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'analysis',
      query: { code: '159915' },
    })
  })

  it('搜索无结果时显示空状态文案', async () => {
    const wrapper = mount(FundList)

    await wrapper.get('[data-test="fund-search"]').setValue('不存在的关键词')

    expect(wrapper.get('[data-test="fund-empty"]').text()).toContain('没有匹配的基金')
  })
})

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import Settings from '../Settings.vue'
import { useColorModeStore } from '../../stores/colorMode'
import { useDisplaySettingsStore } from '../../stores/displaySettings'

describe('Settings', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('渲染页面壳层，采用与其他页面一致的背景和间距', () => {
    const wrapper = mount(Settings)

    expect(wrapper.get('[data-test="settings-shell"]').classes()).toEqual(
      expect.arrayContaining(['min-h-full', 'bg-slate-50', 'p-4', 'md:p-6']),
    )
  })

  it('渲染顶栏，包含标题和副标题', () => {
    const wrapper = mount(Settings)

    const topbar = wrapper.get('[data-test="settings-topbar"]')
    expect(topbar.text()).toContain('系统设置')
    expect(topbar.text()).toContain('管理显示偏好与查看应用信息')
  })

  it('渲染显示偏好卡片，包含红多/绿多切换按钮', () => {
    const wrapper = mount(Settings)

    expect(wrapper.find('[data-test="settings-card-display"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="settings-mode-cn"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="settings-mode-intl"]').exists()).toBe(true)
  })

  it('红多/绿多切换按钮能正确反映 colorMode 当前状态', () => {
    const wrapper = mount(Settings)
    const colorMode = useColorModeStore()

    expect(colorMode.mode).toBe('cn')
    expect(wrapper.get('[data-test="settings-mode-cn"]').classes()).toContain('bg-white')
  })

  it('点击绿多按钮后 colorMode store 切换到 intl', async () => {
    const wrapper = mount(Settings)
    const colorMode = useColorModeStore()

    await wrapper.get('[data-test="settings-mode-intl"]').trigger('click')

    expect(colorMode.mode).toBe('intl')
  })

  it('点击红多按钮后 colorMode store 切换到 cn', async () => {
    const wrapper = mount(Settings)
    const colorMode = useColorModeStore()
    colorMode.setMode('intl')

    await wrapper.get('[data-test="settings-mode-cn"]').trigger('click')

    expect(colorMode.mode).toBe('cn')
  })

  it('渲染卡片数量下拉，默认值为 10', () => {
    const wrapper = mount(Settings)

    const select = wrapper.get('[data-test="settings-card-count"]')
    expect((select.element as HTMLSelectElement).value).toBe('10')
  })

  it('卡片数量下拉包含 4 个选项：6/8/10/12', () => {
    const wrapper = mount(Settings)

    const options = wrapper.get('[data-test="settings-card-count"]').findAll('option')
    expect(options.map(o => o.element.value)).toEqual(['6', '8', '10', '12'])
  })

  it('切换卡片数量后 displaySettings store 更新', async () => {
    const wrapper = mount(Settings)
    const displaySettings = useDisplaySettingsStore()

    await wrapper.get('[data-test="settings-card-count"]').setValue('8')

    expect(displaySettings.cardCount).toBe(8)
  })

  it('渲染关于卡片，包含软件名称、版本、协议、联网行为', () => {
    const wrapper = mount(Settings)

    const about = wrapper.get('[data-test="settings-card-about"]')
    expect(about.text()).toContain('FUNDFLOW')
    expect(about.text()).toContain('v0.0.1 预览版')
    expect(about.text()).toContain('GPLv3')
    expect(about.text()).toContain('仅抓取行情')
  })

  it('渲染隐私与免责声明卡片，包含三段声明文字', () => {
    const wrapper = mount(Settings)

    const disclaimer = wrapper.get('[data-test="settings-card-disclaimer"]')
    expect(disclaimer.text()).toContain('隐私保护')
    expect(disclaimer.text()).toContain('数据安全')
    expect(disclaimer.text()).toContain('投资风险')
    expect(disclaimer.text()).toContain('不收集、上传或存储任何用户个人信息')
    expect(disclaimer.text()).toContain('投资有风险，入市需谨慎')
  })

  it('显示偏好卡片包含配色辅助说明文字', () => {
    const wrapper = mount(Settings)

    expect(wrapper.get('[data-test="settings-card-display"]').text()).toContain('所有页面的涨跌颜色同步生效')
  })

  it('显示偏好卡片包含卡片数量辅助说明文字', () => {
    const wrapper = mount(Settings)

    expect(wrapper.get('[data-test="settings-card-display"]').text()).toContain('信号卡片')
    expect(wrapper.get('[data-test="settings-card-display"]').text()).toContain('入口卡片')
  })
})

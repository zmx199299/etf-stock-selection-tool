<template>
  <section data-test="settings-shell" class="min-h-full bg-slate-50 p-4 md:p-6">
    <div class="flex w-full flex-col gap-4">
      <!-- 顶栏 -->
      <header
        data-test="settings-topbar"
        class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5"
      >
        <div class="space-y-1">
          <h1 class="text-2xl font-semibold tracking-tight text-slate-900">系统设置</h1>
          <p class="text-sm text-slate-500">管理显示偏好与查看应用信息</p>
        </div>
      </header>

      <!-- 卡片一：显示偏好 -->
      <div
        data-test="settings-card-display"
        class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 class="text-lg font-semibold text-slate-900">显示偏好</h2>

        <!-- 涨跌配色 -->
        <div class="mt-5 space-y-2">
          <label class="text-sm font-medium text-slate-700">涨跌配色</label>
          <div class="inline-flex rounded-xl bg-slate-100 p-1">
            <button
              data-test="settings-mode-cn"
              type="button"
              class="rounded-lg px-3 py-2 text-sm font-medium transition"
              :class="colorMode.mode === 'cn' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
              @click="colorMode.setMode('cn')"
            >
              红多
            </button>
            <button
              data-test="settings-mode-intl"
              type="button"
              class="rounded-lg px-3 py-2 text-sm font-medium transition"
              :class="colorMode.mode === 'intl' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
              @click="colorMode.setMode('intl')"
            >
              绿多
            </button>
          </div>
          <p class="text-xs text-slate-400">切换后所有页面的涨跌颜色同步生效。也可以在「全量基金」和「技术分析」页面顶栏快捷切换。</p>
        </div>

        <!-- 卡片数量 -->
        <div class="mt-5 space-y-2">
          <label class="text-sm font-medium text-slate-700">首页/分析入口卡片数量</label>
          <select
            data-test="settings-card-count"
            :value="String(displaySettings.cardCount)"
            class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-300 focus:ring-2 focus:ring-slate-200"
            @change="onCardCountChange"
          >
            <option value="6">6 支</option>
            <option value="8">8 支</option>
            <option value="10">10 支（默认）</option>
            <option value="12">12 支</option>
          </select>
          <p class="text-xs text-slate-400">同时控制「今日行情」信号卡片和「技术分析」入口卡片的显示数量</p>
        </div>
      </div>

      <!-- 卡片二：关于 -->
      <div
        data-test="settings-card-about"
        class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 class="text-lg font-semibold text-slate-900">关于</h2>
        <div class="mt-4 grid grid-cols-2 gap-3">
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">软件名称</p>
            <p class="mt-1 text-base font-semibold italic text-blue-600">FUNDFLOW</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">版本</p>
            <p class="mt-1 text-base font-semibold text-slate-900">v0.0.1 预览版</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">开源协议</p>
            <p class="mt-1 text-base font-semibold text-slate-900">GPLv3</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">联网行为</p>
            <p class="mt-1 text-base font-semibold text-slate-900">仅抓取行情 + 跳转雪球</p>
          </div>
        </div>
      </div>

      <!-- 卡片三：隐私与免责声明 -->
      <div
        data-test="settings-card-disclaimer"
        class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 class="text-lg font-semibold text-slate-900">隐私与免责声明</h2>
        <div class="mt-4 space-y-4">
          <div class="flex gap-3">
            <span class="mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-blue-500"></span>
            <div>
              <p class="text-sm font-medium text-slate-700">隐私保护</p>
              <p class="mt-1 text-sm text-slate-500">本软件为本地运行的单机工具，不收集、上传或存储任何用户个人信息。联网行为仅限于：获取市场行情数据、跳转至雪球网站查看基金详情。除此之外不与任何外部服务器通信。</p>
            </div>
          </div>
          <div class="flex gap-3">
            <span class="mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-yellow-500"></span>
            <div>
              <p class="text-sm font-medium text-yellow-600">数据安全</p>
              <p class="mt-1 text-sm text-yellow-600">本软件仍处于早期开发阶段（预览版），开发者无法对数据的安全性和真实性做出保证。所有行情数据仅供参考，请用户自行核实。</p>
            </div>
          </div>
          <div class="flex gap-3">
            <span class="mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-red-500"></span>
            <div>
              <p class="text-sm font-medium text-red-500">投资风险</p>
              <p class="mt-1 text-sm text-red-500">投资有风险，入市需谨慎。本软件提供的所有分析结论、策略建议仅作为辅助参考，不构成任何投资建议。开发者不对任何投资决策及其结果承担责任，用户需风险自担。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import { useColorModeStore } from '../stores/colorMode'
import { useDisplaySettingsStore } from '../stores/displaySettings'
import type { CardCount } from '../stores/displaySettings'

const colorMode = useColorModeStore()
const displaySettings = useDisplaySettingsStore()

function onCardCountChange(event: Event) {
  const value = Number((event.target as HTMLSelectElement).value)
  displaySettings.setCardCount(value as CardCount)
}

onMounted(() => {
  colorMode.hydrate()
  displaySettings.hydrate()
})
</script>

<template>
  <section data-test="dashboard-shell" class="min-h-full bg-slate-50 p-4 md:p-6">
    <div class="flex w-full flex-col gap-4">
      <header
        data-test="dashboard-topbar"
        class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5"
      >
        <div
          data-test="dashboard-topbar-flex"
          class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"
        >
          <div data-test="dashboard-topbar-left" class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight text-slate-900">今日监测信号总览</h1>
            <p class="text-sm text-slate-500">共监测{{ signals.length }}支，当前符合规则{{ filteredSignals.length }}支</p>
          </div>

          <div
            data-test="dashboard-topbar-right"
            class="flex flex-col gap-3 md:flex-row md:items-center lg:w-[380px] lg:flex-none"
          >
            <div data-test="dashboard-tab-group" class="inline-flex rounded-xl bg-slate-100 p-1">
              <button @click="activeTab = 'all'" :class="activeTab === 'all' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-900'" class="f-btn rounded-lg px-3 py-2 text-sm font-medium transition">全部</button>
              <button @click="activeTab = 'T+0'" :class="activeTab === 'T+0' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-900'" class="f-btn rounded-lg px-3 py-2 text-sm font-medium transition">T+0</button>
              <button @click="activeTab = 'T+1'" :class="activeTab === 'T+1' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-900'" class="f-btn rounded-lg px-3 py-2 text-sm font-medium transition">T+1</button>
            </div>

            <div
              data-test="dashboard-control-slot"
              aria-hidden="true"
              class="hidden h-[42px] rounded-xl border border-transparent md:block md:w-64 lg:flex-1"
            ></div>
          </div>
        </div>
      </header>

      <div
        data-test="dashboard-card-grid"
        class="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6"
      >
        
        <div v-for="signal in filteredSignals" :key="signal.code" @click="goToAnalysis(signal.code)" class="fund-card bg-white rounded-[32px] p-6 border border-gray-100 shadow-sm cursor-pointer relative group h-full">
            <div :class="signal.tPlus === 'T+0' ? 'bg-blue-50 text-blue-500 border-blue-100' : 'bg-gray-50 text-gray-400 border-gray-100'" class="absolute top-5 right-5 px-2 py-0.5 text-[10px] font-bold rounded-md border">{{ signal.tPlus === 'T+0' ? 'T + 0' : 'T + 1' }}</div>
            <div class="pr-12 mb-5">
              <span class="text-base font-bold text-gray-900 block truncate">{{ signal.name }}</span>
              <span class="text-[10px] font-mono text-gray-400 font-medium">{{ formatCode(signal.code) }}</span>
            </div>
            
            <div class="flex justify-between items-end mb-6">
                <div class="flex flex-col">
                    <span :data-test="`dashboard-change-${signal.code}`" :class="paletteFor(signal.changePct).valueClass" class="text-3xl font-black leading-none tabular-nums">{{ formatPercent(signal.changePct) }}</span>
                    <div class="flex gap-4 mt-3">
                        <div class="flex flex-col">
                          <span class="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">净值(IOPV)</span>
                          <span class="text-[13px] font-mono font-bold text-gray-700 leading-tight">{{ formatDecimal(signal.latestNav) }}</span>
                          <span class="text-[10px] font-mono text-gray-400 mt-0.5">{{ formatNavDate(signal.navDate) }}</span>
                        </div>
                        <div class="flex flex-col border-l border-gray-100 pl-4">
                          <span :class="paletteFor(signal.premiumRate ?? 0).softTextClass" class="text-[10px] opacity-80 font-bold uppercase tracking-tighter">实时溢价</span>
                          <span :data-test="`dashboard-premium-${signal.code}`" :class="paletteFor(signal.premiumRate ?? 0).valueClass" class="text-[13px] font-mono font-bold leading-tight">{{ formatPercent(signal.premiumRate) }}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="bg-gray-50/80 rounded-2xl p-4 space-y-2 mb-6 border border-gray-100/50">
                <div class="flex justify-between text-xs text-gray-500 font-medium"><span>明日买入</span><span class="mono font-bold text-gray-900">{{ formatDecimal(signal.buyPrice) }}</span></div>
                <div class="flex justify-between text-xs text-gray-500 font-medium"><span>建议卖出</span><span class="mono font-bold text-gray-900">{{ formatDecimal(signal.sellPrice) }}</span></div>
            </div>
            
            <div class="h-1.5 w-full bg-gray-100 rounded-full flex overflow-hidden">
                <div :data-test="`dashboard-risk-bearish-${signal.code}`" :class="barClass('bearish')" :style="{ width: riskWidth(signal) + '%' }"></div>
                <div :data-test="`dashboard-risk-bullish-${signal.code}`" :class="[barClass('bullish'), 'flex-1 ml-0.5']"></div>
            </div>
        </div>

      </div>

      <!-- 空状态 -->
      <div v-if="filteredSignals.length === 0" class="text-center py-20 text-gray-300 text-sm italic">
        暂无交易信号
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useColorModeStore } from '../stores/colorMode'
import {
  loadSharedFundCards,
  type SharedFundCard,
} from '../utils/dashboardSignals'
import { getDirectionPalette, numericToDirection } from '../utils/marketColors'

const router = useRouter()
const colorMode = useColorModeStore()

const signals = ref<SharedFundCard[]>([])
const activeTab = ref<'all' | 'T+0' | 'T+1'>('all')

const filteredSignals = computed(() => {
  if (activeTab.value === 'all') return signals.value
  return signals.value.filter(s => s.tPlus === activeTab.value)
})

function riskWidth(signal: SharedFundCard): number {
  const maxLossPct = signal.maxLossPct ?? 0
  const expectedProfitPct = signal.expectedProfitPct ?? 0
  const total = maxLossPct + expectedProfitPct
  if (total === 0) return 33.33 // 默认 1/3，与 HTML 参考一致
  return Math.round((maxLossPct / total) * 100)
}

function paletteFor(value: number) {
  return getDirectionPalette(colorMode.mode, numericToDirection(value))
}

function barClass(direction: 'bullish' | 'bearish') {
  return getDirectionPalette(colorMode.mode, direction).barClass
}

function formatCode(code: string): string {
  const suffix = code.startsWith('6') || code.startsWith('5') ? '.SH' : '.SZ'
  return code + suffix
}

function formatDecimal(value: number | null): string {
  return value != null ? value.toFixed(3) : '加载中'
}

function formatPercent(value: number | null): string {
  if (value == null) return '加载中'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatNavDate(dateStr: string | null): string {
  if (!dateStr) return '加载中'
  return dateStr.replace(/-/g, '').slice(2)
}

function goToAnalysis(code: string) {
  router.push({ name: 'analysis', query: { code } })
}

async function fetchSignals() {
  signals.value = (await loadSharedFundCards()).slice(0, 10)
}

onMounted(() => {
  fetchSignals()
})
</script>

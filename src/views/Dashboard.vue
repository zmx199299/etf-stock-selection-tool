<template>
  <div>
    <header class="bg-white/90 backdrop-blur-md sticky top-0 md:top-6 z-40 mx-4 md:mx-8 mt-4 md:mt-6 p-6 rounded-[24px] border border-gray-100 shadow-sm flex flex-col lg:flex-row items-center justify-between gap-6">
        <div class="flex items-center gap-8 w-full lg:w-auto">
            <div class="flex flex-col">
                <span class="text-[10px] text-gray-400 font-bold uppercase tracking-widest">今日监测</span>
                <span class="text-lg font-black italic">{{ signals.length }} <span class="text-xs font-normal not-italic text-gray-300">支</span></span>
            </div>
            <div class="flex flex-col border-l pl-8 border-gray-100">
                <span class="text-[10px] text-red-400 font-bold uppercase tracking-widest">符合规则</span>
                <span class="text-lg font-black text-red-500 italic">{{ filteredSignals.length }}</span>
            </div>
        </div>

        <div class="flex items-center bg-gray-100 p-1 rounded-xl w-full xl:w-auto">
            <button @click="activeTab = 'all'" :class="activeTab === 'all' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-400 hover:text-gray-600'" class="f-btn flex-1 xl:flex-none px-8 py-2 text-xs font-bold rounded-lg transition-all">全部</button>
            <button @click="activeTab = 'T+0'" :class="activeTab === 'T+0' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-400 hover:text-gray-600'" class="f-btn flex-1 xl:flex-none px-8 py-2 text-xs font-bold rounded-lg transition-all">T + 0</button>
            <button @click="activeTab = 'T+1'" :class="activeTab === 'T+1' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-400 hover:text-gray-600'" class="f-btn flex-1 xl:flex-none px-8 py-2 text-xs font-bold rounded-lg transition-all">T + 1</button>
        </div>
    </header>

    <div class="p-4 md:p-8 columns-1 md:columns-2 lg:columns-3 xl:columns-4 2xl:columns-6 gap-6 space-y-6">
        
        <div v-for="signal in filteredSignals" :key="signal.code" @click="goToAnalysis(signal.code)" class="fund-card break-inside-avoid bg-white rounded-[32px] p-6 border border-gray-100 shadow-sm cursor-pointer relative group">
            <div :class="signal.t_plus === 'T+0' ? 'bg-blue-50 text-blue-500 border-blue-100' : 'bg-gray-50 text-gray-400 border-gray-100'" class="absolute top-5 right-5 px-2 py-0.5 text-[10px] font-bold rounded-md border">{{ signal.t_plus === 'T+0' ? 'T + 0' : 'T + 1' }}</div>
            <div class="pr-12 mb-5">
              <span class="text-base font-bold text-gray-900 block truncate">{{ signal.name }}</span>
              <span class="text-[10px] font-mono text-gray-400 font-medium">{{ formatCode(signal.code) }}</span>
            </div>
            
            <div class="flex justify-between items-end mb-6">
                <div class="flex flex-col">
                    <span :data-test="`dashboard-change-${signal.code}`" :class="paletteFor(signal.change_pct).valueClass" class="text-3xl font-black leading-none tabular-nums">{{ signal.change_pct >= 0 ? '+' : '' }}{{ signal.change_pct.toFixed(2) }}%</span>
                    <div class="flex gap-4 mt-3">
                        <div class="flex flex-col">
                          <span class="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">净值(IOPV)</span>
                          <span class="text-[13px] font-mono font-bold text-gray-700 leading-tight">{{ signal.latest_nav.toFixed(3) }}</span>
                          <span class="text-[10px] font-mono text-gray-400 mt-0.5">{{ formatNavDate(signal.nav_date) }}</span>
                        </div>
                        <div class="flex flex-col border-l border-gray-100 pl-4">
                          <span :class="paletteFor(signal.premium_rate).softTextClass" class="text-[10px] opacity-80 font-bold uppercase tracking-tighter">实时溢价</span>
                          <span :class="paletteFor(signal.premium_rate).valueClass" class="text-[13px] font-mono font-bold leading-tight">{{ signal.premium_rate > 0 ? '+' : '' }}{{ signal.premium_rate.toFixed(2) }}%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="bg-gray-50/80 rounded-2xl p-4 space-y-2 mb-6 border border-gray-100/50">
                <div class="flex justify-between text-xs text-gray-500 font-medium"><span>明日买入</span><span class="mono font-bold text-gray-900">{{ signal.buy_price ? signal.buy_price.toFixed(3) : '加载中' }}</span></div>
                <div class="flex justify-between text-xs text-gray-500 font-medium"><span>建议卖出</span><span class="mono font-bold text-gray-900">{{ signal.sell_price ? signal.sell_price.toFixed(3) : '加载中' }}</span></div>
                <div v-if="signal.stop_loss" class="flex justify-between text-xs pt-2 border-t border-gray-200/50"><span class="text-red-500 font-bold italic">止损点</span><span class="mono font-bold text-red-600">{{ signal.stop_loss.toFixed(3) }}</span></div>
            </div>
            
            <div class="h-1.5 w-full bg-gray-100 rounded-full flex overflow-hidden">
                <div :class="barClass('bearish')" :style="{ width: riskWidth(signal) + '%' }"></div>
                <div :class="[barClass('bullish'), 'flex-1 ml-0.5']"></div>
            </div>
        </div>

    </div>
    
    <!-- 空状态 -->
    <div v-if="filteredSignals.length === 0" class="text-center py-20 text-gray-300 text-sm italic">
      暂无交易信号
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useColorModeStore } from '../stores/colorMode'
import { getDirectionPalette, numericToDirection } from '../utils/marketColors'

const router = useRouter()
const colorMode = useColorModeStore()
const isDev = import.meta.env.DEV || import.meta.env.MODE === 'test'

interface DashboardSignal {
  code: string
  name: string
  t_plus: string
  current_price: number
  change_pct: number
  buy_price: number
  sell_price: number
  stop_loss: number
  latest_nav: number
  nav_date: string
  premium_rate: number
  expected_profit: number
  expected_profit_pct: number
  max_loss: number
  max_loss_pct: number
}

// 模拟数据与你提供的 JS 完全一致
const mockSignals: DashboardSignal[] = [
    { name: "恒生科技ETF", code: "513130", change_pct: 1.85, latest_nav: 0.456, nav_date: "2026-03-30", premium_rate: 0.12, t_plus: "T+0", current_price: 0.456, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "标普500ETF", code: "513500", change_pct: 0.88, latest_nav: 1.234, nav_date: "2026-03-30", premium_rate: 1.45, t_plus: "T+0", current_price: 1.234, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "创业板ETF", code: "159915", change_pct: -1.45, latest_nav: 2.110, nav_date: "2026-03-30", premium_rate: -0.22, t_plus: "T+1", current_price: 2.110, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "纳指100ETF", code: "159941", change_pct: 2.11, latest_nav: 0.889, nav_date: "2026-03-30", premium_rate: 2.10, t_plus: "T+0", current_price: 0.889, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "红利低波ETF", code: "512890", change_pct: 0.23, latest_nav: 1.005, nav_date: "2026-03-30", premium_rate: 0.01, t_plus: "T+1", current_price: 1.005, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "芯片ETF", code: "159995", change_pct: -2.56, latest_nav: 0.998, nav_date: "2026-03-30", premium_rate: -0.45, t_plus: "T+1", current_price: 0.998, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "券商ETF", code: "512000", change_pct: 4.12, latest_nav: 0.852, nav_date: "2026-03-30", premium_rate: 0.88, t_plus: "T+1", current_price: 0.852, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "医疗ETF", code: "512170", change_pct: -0.75, latest_nav: 0.334, nav_date: "2026-03-30", premium_rate: 0.05, t_plus: "T+1", current_price: 0.334, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
    { name: "中概互联网", code: "513050", change_pct: 3.44, latest_nav: 0.912, nav_date: "2026-03-30", premium_rate: 0.67, t_plus: "T+0", current_price: 0.912, buy_price: 0.842, sell_price: 0.910, stop_loss: 0.810, expected_profit: 89.60, expected_profit_pct: 8.2, max_loss: 225.80, max_loss_pct: 3.5 }, // 互联网保留价格用于展示结构
    { name: "游戏ETF", code: "159869", change_pct: -3.11, latest_nav: 1.022, nav_date: "2026-03-30", premium_rate: -1.05, t_plus: "T+1", current_price: 1.022, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 }
];

const signals = ref<DashboardSignal[]>([])
const activeTab = ref<'all' | 'T+0' | 'T+1'>('all')

const filteredSignals = computed(() => {
  if (activeTab.value === 'all') return signals.value
  return signals.value.filter(s => s.t_plus === activeTab.value)
})

function riskWidth(signal: DashboardSignal): number {
  const total = signal.max_loss_pct + signal.expected_profit_pct
  if (total === 0) return 33.33 // 默认 1/3，与 HTML 参考一致
  return Math.round((signal.max_loss_pct / total) * 100)
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

function formatNavDate(dateStr: string): string {
  return dateStr.replace(/-/g, '').slice(2)
}

function goToAnalysis(code: string) {
  router.push({ name: 'analysis', query: { code } })
}

async function fetchSignals() {
  if (isDev) {
    signals.value = mockSignals
  } else {
    try {
      const { invoke } = await import('@tauri-apps/api/core')
      const result = await invoke('invoke_engine', { method: 'get_dashboard_signals', params: {} })
      signals.value = result as DashboardSignal[]
    } catch (e) {
      console.error('获取信号失败:', e)
      signals.value = mockSignals
    }
  }
}

onMounted(() => {
  colorMode.hydrate()
  fetchSignals()
})
</script>

<template>
  <section data-test="fund-shell" class="min-h-full bg-slate-50 p-4 md:p-6">
    <div class="flex w-full flex-col gap-4">
      <div data-test="fund-topbar" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
        <div data-test="fund-topbar-flex" class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div data-test="fund-topbar-left" class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight text-slate-900">全量场内基金（不含货币/债券基金）</h1>
            <p class="text-sm text-slate-500">共监测{{ rows.length }}支</p>
          </div>

          <div data-test="fund-topbar-right" class="flex flex-col gap-3 md:flex-row md:items-center lg:w-[380px] lg:flex-none">
            <div data-test="fund-tab-group" class="inline-flex rounded-xl bg-slate-100 p-1">
              <button
                data-test="mode-cn"
                type="button"
                class="rounded-lg px-3 py-2 text-sm font-medium transition"
                :class="colorMode.mode === 'cn' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
                @click="colorMode.setMode('cn')"
              >
                红多
              </button>
              <button
                data-test="mode-intl"
                type="button"
                class="rounded-lg px-3 py-2 text-sm font-medium transition"
                :class="colorMode.mode === 'intl' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
                @click="colorMode.setMode('intl')"
              >
                绿多
              </button>
            </div>

            <input
              data-test="fund-search"
              v-model="keyword"
              type="text"
              placeholder="搜索基金代码/名称"
              class="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-slate-300 focus:ring-2 focus:ring-slate-200 md:w-64"
            />
          </div>
        </div>
      </div>

      <div
        v-if="startupSyncMessage"
        data-test="startup-sync-alert"
        class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 shadow-sm"
      >
        {{ startupSyncMessage }}
      </div>

      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="overflow-x-auto">
          <table class="min-w-[1480px] w-full text-sm text-slate-700">
            <thead class="bg-slate-50 text-xs uppercase tracking-[0.08em] text-slate-500">
              <tr>
                <th class="px-4 py-3 text-left font-medium">代码/名称</th>
                <th class="px-4 py-3 text-right font-medium">昨收</th>
                <th class="px-4 py-3 text-right font-medium">开盘</th>
                <th class="px-4 py-3 text-right font-medium">现价</th>
                <th class="px-4 py-3 text-right font-medium">最高</th>
                <th class="px-4 py-3 text-right font-medium">最低</th>
                <th class="px-4 py-3 text-right font-medium">波动</th>
                <th class="px-4 py-3 text-right font-medium">涨跌幅</th>
                <th class="px-4 py-3 text-center font-medium">MACD</th>
                <th class="px-4 py-3 text-center font-medium">RSI</th>
                <th class="px-4 py-3 text-center font-medium">BOLL</th>
                <th class="px-4 py-3 text-center font-medium">MA5</th>
                <th class="px-4 py-3 text-center font-medium">MA20</th>
                <th class="px-4 py-3 text-center font-medium">多空</th>
                <th class="px-4 py-3 text-center font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in filteredRows"
                :key="row.code"
                class="border-t border-slate-100 align-middle transition hover:bg-slate-50/80"
              >
                <td class="px-4 py-3">
                  <button
                    :data-test="`xueqiu-${row.code}`"
                    type="button"
                    class="flex flex-col gap-1 text-left transition hover:opacity-80"
                    @click="openXueqiu(row.code)"
                  >
                    <span class="font-mono text-sm font-semibold text-slate-900">{{ row.code }}</span>
                    <span class="text-sm text-slate-600">{{ row.name }}</span>
                  </button>
                </td>
                <td class="px-4 py-3 text-right font-mono text-slate-600">{{ formatPrice(row.prevClose) }}</td>
                <td class="px-4 py-3 text-right font-mono text-slate-600">{{ formatPrice(row.open) }}</td>
                <td class="px-4 py-3 text-right font-mono font-semibold text-slate-900">{{ formatPrice(row.close) }}</td>
                <td class="px-4 py-3 text-right font-mono" :class="getSubtleDirectionClass(row.high - row.prevClose)">{{ formatPrice(row.high) }}</td>
                <td class="px-4 py-3 text-right font-mono" :class="getSubtleDirectionClass(row.low - row.prevClose)">{{ formatPrice(row.low) }}</td>
                <td class="px-4 py-3 text-right font-mono text-slate-600">{{ formatPercent(row.volatility) }}</td>
                <td
                  :data-test="`change-${row.code}`"
                  class="px-4 py-3 text-right font-mono font-semibold"
                  :class="getValueDirectionClass(row.changePct)"
                >
                  {{ formatSignedPercent(row.changePct) }}
                </td>
                <td class="px-4 py-3 text-center" :class="getSoftDirectionClass(row.macd.signal)">{{ row.macd.value }}</td>
                <td class="px-4 py-3 text-center" :class="getSoftDirectionClass(row.rsi.signal)">{{ row.rsi.value }}</td>
                <td class="px-4 py-3 text-center" :class="getSoftDirectionClass(row.boll.signal)">{{ row.boll.value }}</td>
                <td class="px-4 py-3 text-center" :class="getSoftDirectionClass(row.ma5.signal)">{{ row.ma5.value }}</td>
                <td class="px-4 py-3 text-center" :class="getSoftDirectionClass(row.ma20.signal)">{{ row.ma20.value }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center justify-center gap-2">
                    <span class="h-2.5 w-2.5 rounded-full" :class="getScoreDotClass(row.scoreDirection)"></span>
                    <span class="font-mono text-sm font-semibold text-slate-900">{{ row.score }}</span>
                    <span class="text-xs" :class="getSoftDirectionClass(row.scoreDirection)">{{ row.scoreLabel }}</span>
                  </div>
                </td>
                <td class="px-4 py-3 text-center">
                  <button
                    :data-test="`detail-${row.code}`"
                    type="button"
                    class="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900"
                    @click="goToAnalysis(row.code)"
                  >
                    详情分析
                  </button>
                </td>
              </tr>
              <tr v-if="!isInitialLoading && filteredRows.length === 0">
                <td data-test="fund-empty" colspan="15" class="px-4 py-12 text-center text-sm text-slate-500">
                  没有匹配的基金
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useColorModeStore } from '../stores/colorMode'
import { ensureStartupSync, getStartupSyncState } from '../utils/startupSync'
import { buildFundRows, filterFundRows, type FundListItem } from '../utils/fundList'
import {
  getDirectionPalette,
  numericToDirection,
  type MarketDirection,
} from '../utils/marketColors'

const router = useRouter()
const colorMode = useColorModeStore()

const keyword = ref('')
const funds = ref<FundListItem[]>([])
const startupSyncMessage = ref('')
const isInitialLoading = ref(import.meta.env.MODE !== 'test')

function toStartupSyncAlertMessage() {
  const startupSyncState = getStartupSyncState()
  if (startupSyncState.status !== 'error') {
    return ''
  }

  return '启动同步失败，请注意核对当前数据状态'
}

const rows = computed(() => buildFundRows(funds.value))
const filteredRows = computed(() => filterFundRows(rows.value, keyword.value))

function formatPrice(value: number) {
  return value.toFixed(3)
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`
}

function formatSignedPercent(value: number) {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

function getPalette(direction: MarketDirection) {
  return getDirectionPalette(colorMode.mode, direction)
}

function getValueDirectionClass(value: number) {
  return getPalette(numericToDirection(value)).valueClass
}

function getSubtleDirectionClass(value: number) {
  return `${getPalette(numericToDirection(value)).softTextClass} opacity-80`
}

function getSoftDirectionClass(direction: MarketDirection) {
  return getPalette(direction).softTextClass
}

function getScoreDotClass(direction: MarketDirection) {
  return getPalette(direction).dotClass
}

function goToAnalysis(code: string) {
  router.push({
    name: 'analysis',
    query: { code },
  })
}

function openXueqiu(code: string) {
  const market = code.startsWith('5') || code.startsWith('6') ? 'SH' : 'SZ'
  window.open(`https://xueqiu.com/S/${market}${code}`, '_blank', 'noopener,noreferrer')
}

async function fetchFunds() {
  try {
    if (import.meta.env.MODE === 'test' || import.meta.env.DEV) {
      funds.value = []
      return
    }

    await ensureStartupSync()
    startupSyncMessage.value = toStartupSyncAlertMessage()
    const { invoke } = await import('@tauri-apps/api/core')
    const response = await invoke<FundListItem[]>('invoke_engine', {
      method: 'get_fund_list',
      params: {},
    })

    funds.value = Array.isArray(response) ? response : []
  } catch {
    funds.value = []
  } finally {
    isInitialLoading.value = false
  }
}

onMounted(() => {
  colorMode.hydrate()
  void fetchFunds()
})
</script>

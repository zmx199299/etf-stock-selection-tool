<template>
  <section data-test="analysis-shell" class="min-h-full bg-slate-50 p-4 md:p-6">
    <div class="flex w-full flex-col gap-4">
      <header data-test="analysis-topbar" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight text-slate-900">技术分析</h1>
            <p class="text-sm text-slate-500">{{ headerDescription }}</p>
          </div>

          <div data-test="analysis-topbar-right" class="flex flex-col gap-3 md:flex-row md:items-center lg:w-[380px] lg:flex-none">
            <div class="inline-flex rounded-xl bg-slate-100 p-1">
              <button
                data-test="analysis-mode-cn"
                type="button"
                class="rounded-lg px-3 py-2 text-sm font-medium transition"
                :class="colorMode.mode === 'cn' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
                @click="colorMode.setMode('cn')"
              >
                红多
              </button>
              <button
                data-test="analysis-mode-intl"
                type="button"
                class="rounded-lg px-3 py-2 text-sm font-medium transition"
                :class="colorMode.mode === 'intl' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
                @click="colorMode.setMode('intl')"
              >
                绿多
              </button>
            </div>

            <div class="relative w-full md:w-64">
              <input
                data-test="analysis-search"
                v-model="keyword"
                type="text"
                placeholder="搜索基金代码/名称"
                class="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-slate-300 focus:ring-2 focus:ring-slate-200"
              />
              <div
                v-if="keyword.trim() && candidates.length > 0"
                class="absolute left-0 top-[calc(100%+0.5rem)] z-10 w-full rounded-2xl border border-slate-200 bg-white p-2 shadow-lg"
              >
                <button
                  v-for="candidate in candidates"
                  :key="`topbar-${candidate.code}`"
                  :data-test="`analysis-pick-${candidate.code}`"
                  type="button"
                  class="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left transition hover:bg-slate-50"
                  @click="selectCode(candidate.code)"
                >
                  <span class="text-sm font-medium text-slate-900">{{ candidate.name }}</span>
                  <span class="text-xs text-slate-500">{{ candidate.code }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <section
        v-if="showEntryStrip"
        data-test="analysis-entry-strip"
        class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <div class="flex flex-wrap gap-3">
          <button
            v-for="card in entryCards"
            :key="card.code"
            :data-test="`analysis-entry-card-${card.code}`"
            type="button"
            class="min-w-[160px] flex-1 rounded-2xl border px-4 py-3 text-left transition md:max-w-[220px]"
            :class="activeCode === card.code ? 'border-slate-900 bg-slate-900 text-white shadow-sm' : 'border-slate-200 bg-slate-50 text-slate-900 hover:border-slate-300 hover:bg-white'"
            @click="selectCode(card.code)"
          >
            <div class="text-sm font-semibold">{{ card.name }}</div>
            <div class="mt-1 text-xs" :class="activeCode === card.code ? 'text-slate-200' : 'text-slate-500'">{{ card.code }}</div>
          </button>
        </div>
      </section>

      <div
        v-if="!activeAnalysis"
        data-test="analysis-empty-state"
        class="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm"
      >
        <h2 class="text-xl font-semibold text-slate-900">请选择基金</h2>
        <p class="mt-2 text-sm text-slate-500">请从顶部卡片或搜索选择基金，再查看对应的技术分析内容。</p>
        <p v-if="keyword.trim() && candidates.length === 0" data-test="analysis-empty-hint" class="mt-3 text-sm text-slate-400">
          未找到匹配基金，请更换代码或名称关键字。
        </p>
      </div>

      <template v-else>
        <div data-test="analysis-hero-grid" class="grid gap-4 lg:grid-cols-[2fr_3fr]">
          <div data-test="analysis-section-summary" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="space-y-4">
              <div class="space-y-2">
                <p class="text-sm font-medium text-slate-500">摘要概览</p>
                <div class="space-y-1">
                  <h2 class="text-2xl font-semibold text-slate-900">{{ activeAnalysis.name }}</h2>
                  <p class="text-sm text-slate-500">{{ activeAnalysis.code }}</p>
                </div>
              </div>

              <div class="grid gap-3 sm:grid-cols-2">
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">市场</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.market }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">最新价</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.price }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">涨跌幅</p>
                  <p class="mt-1 text-base font-semibold" :class="changePalette.valueClass">{{ activeAnalysis.change }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">参考净值</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.iopv }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">溢价率</p>
                  <p class="mt-1 text-base font-semibold" :class="premiumPalette.valueClass">{{ activeAnalysis.premium }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">风险等级</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.riskLevel }}</p>
                </div>
              </div>
            </div>
          </div>

          <div data-test="analysis-section-strategy" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="space-y-4">
              <div class="space-y-2">
                <p class="text-sm font-medium text-slate-500">策略建议</p>
                <h2 class="text-2xl font-semibold text-slate-900">{{ activeAnalysis.strategy.conclusion }}</h2>
              </div>

              <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">买入区间</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.strategy.buyZone }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">卖出区间</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.strategy.sellZone }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">仓位建议</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.strategy.position }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">止盈止损</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.strategy.stopLoss }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3">
                  <p class="text-xs text-slate-500">持有周期</p>
                  <p class="mt-1 text-base font-semibold text-slate-900">{{ activeAnalysis.strategy.holdingPeriod }}</p>
                </div>
                <div class="rounded-xl bg-slate-50 p-3 md:col-span-2 xl:col-span-1">
                  <p class="text-xs text-slate-500">风险提示</p>
                  <p class="mt-1 text-sm font-medium leading-6 text-slate-900">{{ activeAnalysis.strategy.riskNote }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <section data-test="analysis-section-chart" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="space-y-4">
            <div class="space-y-3">
              <h2 class="text-lg font-semibold text-slate-900">图表研判</h2>
              <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <label class="flex items-center gap-2 text-sm text-slate-500">
                  <span>周期</span>
                  <select
                    data-test="analysis-period-select"
                    v-model="activePeriodKey"
                    class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-300 focus:ring-2 focus:ring-slate-200"
                  >
                    <option v-for="period in periodOptions" :key="period.key" :value="period.key">
                      {{ period.optionLabel }}
                    </option>
                  </select>
                </label>
                <p data-test="analysis-period-summary" class="text-sm text-slate-500">{{ activePeriodSummary }}</p>
              </div>
              <p data-test="analysis-chart-summary" class="text-sm text-slate-500">{{ activePeriod?.chartSummary }}</p>
            </div>
            <div class="grid gap-4 xl:grid-cols-[2fr_1fr]">
              <div data-test="analysis-chart-mock" class="rounded-2xl border border-slate-200 bg-slate-50 p-6">
                <div class="flex items-center justify-between text-sm font-medium text-slate-700">
                  <span>{{ chartTitle }}</span>
                  <span class="text-xs text-slate-400">仅展示版式层级</span>
                </div>
                <div class="mt-4 rounded-xl border border-slate-200 bg-white p-4 h-[400px]">
                  <v-chart class="h-full w-full" :option="chartOption" autoresize />
                </div>
              </div>

              <div class="rounded-2xl bg-slate-50 p-5 text-sm text-slate-600">
                <div class="text-xs uppercase tracking-[0.08em] text-slate-400">图旁解读</div>
                <div data-test="analysis-chart-headline" class="mt-3 text-base font-medium text-slate-900">{{ activePeriod?.chartHeadline }}</div>
              </div>
            </div>
          </div>
        </section>

        <section data-test="analysis-section-metrics" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="space-y-4">
            <div>
              <h2 class="text-lg font-semibold text-slate-900">技术指标结论</h2>
              <p class="mt-1 text-sm text-slate-500">使用克制的信息卡对关键指标做总结，不抢主视线。</p>
            </div>
            <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <article
                v-for="(metric, index) in displayMetrics"
                :key="`${metric.label}-${index}`"
                data-test="analysis-metric-card"
                class="rounded-2xl bg-slate-50 p-5"
              >
                <div class="flex items-center justify-between">
                  <div
                    :data-test="`analysis-metric-label-${index}`"
                    class="text-xs uppercase tracking-[0.08em] text-slate-400"
                  >
                    {{ metric.label }}
                  </div>
                  <span
                    :data-test="`analysis-metric-dot-${index}`"
                    class="h-2.5 w-2.5 rounded-full"
                    :class="getMetricPalette(metric.tone).dotClass"
                  ></span>
                </div>
                <div
                  :data-test="`analysis-metric-value-${metric.label}`"
                  class="mt-3 text-lg font-semibold"
                  :class="getMetricPalette(metric.tone).valueClass"
                >
                  <span
                    :data-test="`analysis-metric-value-${index}`"
                    :class="getMetricPalette(metric.tone).valueClass"
                  >
                    {{ metric.value }}
                  </span>
                </div>
                <div :data-test="`analysis-metric-summary-${index}`" class="mt-2 text-sm text-slate-600">{{ metric.summary }}</div>
              </article>
            </div>
          </div>
        </section>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useColorModeStore } from '../stores/colorMode'
import { useDisplaySettingsStore } from '../stores/displaySettings'
import { invoke } from '@tauri-apps/api/core'
import { buildIntradayOption, buildKLineOption } from '../utils/chartAdapter'
import { getAnalysisEntryCards, loadSharedFundCards, type SharedFundCard } from '../utils/dashboardSignals'
import { getDirectionPalette, numericToDirection, type MarketDirection } from '../utils/marketColors'

const route = useRoute()
const router = useRouter()
const colorMode = useColorModeStore()
const displaySettings = useDisplaySettingsStore()

const keyword = ref('')
const candidates = ref<any[]>([])
const sharedCards = ref<SharedFundCard[]>([])
const activePeriodKey = ref('day')

const routeCode = computed(() => {
  const raw = route.query.code
  return typeof raw === 'string' && raw ? raw : null
})

const entryCards = computed<SharedFundCard[]>(() => {
  return getAnalysisEntryCards(routeCode.value, sharedCards.value, displaySettings.cardCount)
})

const activeCode = computed(() => routeCode.value)
const activeAnalysis = ref<any>(null)
const activePeriod = computed(() => activeAnalysis.value?.periods[activePeriodKey.value] ?? null)
const isIntradayChart = computed(() => activePeriodKey.value === 'intraday')
const showEntryStrip = computed(() => !routeCode.value && entryCards.value.length > 0)
const periodOptions = computed(() => {
  if (!activeAnalysis.value) {
    return []
  }
  const keys = ['intraday', 'day', 'm5', 'm60', 'm120', 'week', 'month', 'quarter', 'year']
  return keys.map((key) => ({
    key,
    optionLabel: getPeriodDisplayLabel(key, activeAnalysis.value?.periods[key]?.label),
  }))
})
const activePeriodChartLabel = computed(() => getPeriodDisplayLabel(activePeriodKey.value, activePeriod.value?.label))
const chartTitle = computed(() => {
  const shapeLabel = isIntradayChart.value ? '分时图' : 'K 线图'
  return `${activePeriodChartLabel.value} / ${shapeLabel}`
})
const activePeriodSummary = computed(() => {
  if (!activePeriod.value) {
    return ''
  }

  const periodLabel = getPeriodDisplayLabel(activePeriodKey.value, activePeriod.value.label)
  return `${periodLabel}：${activePeriod.value.summary}`
})
const displayMetrics = computed(() => {
  if (!activePeriod.value) {
    return []
  }

  const activeMetrics = activePeriod.value.metrics || []
  const placeholders = Array.from({ length: Math.max(4 - activeMetrics.length, 0) }, (_, index) => ({
    label: `占位指标 ${index + 1}`,
    value: '--',
    summary: '当前周期指标待补充',
    tone: 'neutral' as const,
  }))

  return [...activeMetrics, ...placeholders].slice(0, 4)
})

const changePalette = computed(() => {
  const value = Number(activeAnalysis.value?.change.replace('%', '') ?? '0')
  return getDirectionPalette(colorMode.mode, numericToDirection(value))
})

const premiumPalette = computed(() => {
  const value = Number(activeAnalysis.value?.premium.replace('%', '') ?? '0')
  return getDirectionPalette(colorMode.mode, numericToDirection(value))
})

const headerDescription = computed(() => {
  if (activeAnalysis.value) {
    return `${activeAnalysis.value.name} ${activeAnalysis.value.code}`
  }

  return '先搜索或选择基金，再查看技术分析内容'
})

function selectCode(code: string) {
  keyword.value = ''
  activePeriodKey.value = 'day'
  void router.push({
    name: 'analysis',
    query: { code },
  })
}

function getMetricPalette(direction: MarketDirection) {
  return getDirectionPalette(colorMode.mode, direction)
}

function getPeriodDisplayLabel(key: string, fallbackLabel?: string) {
  const labelMap: Record<string, string> = {
    intraday: '分时',
    day: '日K',
    m5: '5分',
    m60: '60分',
    m120: '120分',
    week: '周K',
    month: '月K',
    quarter: '季K',
    year: '年K',
  }

  return labelMap[key] ?? fallbackLabel ?? 'K 线'
}

const fetchAnalysisData = async (code: string) => {
  activeAnalysis.value = null
  try {
    const res = await invoke('invoke_engine', {
      method: 'get_analysis_data',
      params: { code }
    })
    if (res) activeAnalysis.value = res
  } catch (err) {
    console.error(err)
  }
}

watch(routeCode, (code) => {
  activePeriodKey.value = 'day'
  if (code) {
    keyword.value = ''
    fetchAnalysisData(code)
  } else {
    activeAnalysis.value = null
  }
}, { immediate: true })

watch(keyword, async (kw) => {
  if (!kw.trim()) {
    candidates.value = []
    return
  }
  try {
    candidates.value = await invoke('invoke_engine', { method: 'search_funds', params: { keyword: kw } })
  } catch (e) {
    candidates.value = []
  }
})

const chartOption = computed(() => {
  if (!activePeriod.value) return {}
  if (isIntradayChart.value) return buildIntradayOption(activePeriod.value, colorMode.mode)
  return buildKLineOption(activePeriod.value, colorMode.mode)
})

onMounted(async () => {
  displaySettings.hydrate()
  sharedCards.value = await loadSharedFundCards()
})
</script>

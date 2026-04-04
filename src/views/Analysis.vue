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
                <div class="mt-4 rounded-xl border border-slate-200 bg-white p-4">
                  <div class="grid grid-cols-[auto_1fr] gap-3">
                    <div class="flex h-40 flex-col justify-between pb-3 text-xs text-slate-400">
                      <span
                        v-for="price in activePeriod?.priceAxis ?? []"
                        :key="price"
                        data-test="analysis-price-axis-label"
                      >
                        {{ price }}
                      </span>
                    </div>

                    <div>
                      <div
                        data-test="analysis-chart-hit-area"
                        class="relative h-40 rounded-lg bg-[linear-gradient(180deg,#f8fafc_0%,#ffffff_100%)] px-2 pb-3 pt-3"
                        @mouseleave="hideCandleTooltip"
                      >
                        <div class="absolute inset-x-2 inset-y-3 flex flex-col justify-between">
                          <div v-for="price in activePeriod?.priceAxis ?? []" :key="`grid-${price}`" class="border-t border-dashed border-slate-200"></div>
                        </div>

                        <div v-if="isIntradayChart" class="relative z-10 h-full">
                          <svg class="h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                            <polyline
                              data-test="analysis-intraday-line"
                              fill="none"
                              :stroke="intradayLineColor"
                              stroke-width="2"
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              :points="intradayLinePath"
                            />
                            <polyline
                              data-test="analysis-intraday-avg-line"
                              fill="none"
                              :stroke="intradayAvgLineColor"
                              stroke-width="2"
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-dasharray="4 3"
                              :points="intradayAvgLinePath"
                            />
                          </svg>
                          <div class="absolute inset-0 z-20 flex">
                            <div
                              v-for="(_, index) in intradayTooltipPoints"
                              :key="`intraday-hitbox-${index}`"
                              :data-test="`analysis-intraday-hitbox-${index}`"
                              class="h-full w-full cursor-pointer bg-transparent"
                              @mouseenter="showIntradayTooltip(index, $event)"
                            ></div>
                          </div>
                        </div>

                        <div v-else class="relative z-10 flex h-full items-end gap-2">
                          <div
                            v-for="(candle, index) in chartCandles"
                            :key="`candle-${index}`"
                            data-test="analysis-chart-candle"
                            class="relative flex w-full items-end justify-center"
                          >
                            <div
                              :data-test="`analysis-chart-candle-hitbox-${index}`"
                              class="absolute inset-0 z-20 cursor-pointer bg-transparent"
                              @mouseenter="showCandleTooltip(index, $event)"
                            ></div>
                            <div
                              :data-test="`analysis-chart-candle-${index}-line`"
                              class="absolute bottom-2 w-px bg-slate-300"
                              :style="{ height: `${candle.lineHeight}px` }"
                            ></div>
                            <div
                              :data-test="`analysis-chart-candle-${index}-body`"
                              class="w-3 rounded-sm"
                              :class="getCandlePalette(candle.direction).barClass"
                              :style="{ height: `${candle.bodyHeight}px` }"
                            ></div>
                          </div>
                        </div>

                        <div
                          v-if="hoveredTooltip"
                          data-test="analysis-chart-tooltip"
                          class="pointer-events-none absolute z-30 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow-lg"
                          :style="tooltipStyle"
                        >
                          <template v-if="hoveredTooltip.type === 'candle'">
                            <div>日期：{{ hoveredTooltip.label }}</div>
                            <div>开盘：{{ formatTooltipPrice(hoveredTooltip.open) }}</div>
                            <div>收盘：{{ formatTooltipPrice(hoveredTooltip.close) }}</div>
                            <div>最高：{{ formatTooltipPrice(hoveredTooltip.high) }}</div>
                            <div>最低：{{ formatTooltipPrice(hoveredTooltip.low) }}</div>
                          </template>
                          <template v-else>
                            <div>时间：{{ hoveredTooltip.label }}</div>
                            <div>价格：{{ formatTooltipPrice(hoveredTooltip.price) }}</div>
                            <div>均价：{{ formatTooltipPrice(hoveredTooltip.average) }}</div>
                          </template>
                        </div>
                      </div>

                      <div class="mt-2 flex justify-between px-2 text-xs text-slate-400">
                        <span
                          v-for="(time, index) in activePeriod?.timeAxis ?? []"
                          :key="`time-${activePeriodKey}-${index}-${time}`"
                          data-test="analysis-time-axis-label"
                        >
                          {{ time }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="mt-4 flex h-16 items-end gap-2 px-2">
                  <div
                    :data-test="`analysis-chart-volume-bar-${index}`"
                    v-for="(height, index) in chartVolumes"
                    :key="`volume-${index}`"
                    class="w-full rounded-t"
                    :class="getCandlePalette(chartCandles[index]?.direction ?? 'neutral').barClass"
                    :style="{ height: `${height}%` }"
                  ></div>
                  </div>
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
import {
  ANALYSIS_PERIOD_KEYS,
  getAnalysisMockByCode,
  searchAnalysisCandidates,
  type AnalysisPeriodKey,
} from '../utils/analysisMock'
import { getAnalysisEntryCards, loadSharedFundCards, type SharedFundCard } from '../utils/dashboardSignals'
import { getDirectionPalette, numericToDirection, type MarketDirection } from '../utils/marketColors'

const route = useRoute()
const router = useRouter()
const colorMode = useColorModeStore()
const displaySettings = useDisplaySettingsStore()

const keyword = ref('')
const sharedCards = ref<SharedFundCard[]>([])
const activePeriodKey = ref<AnalysisPeriodKey>('day')
const hoveredCandleIndex = ref<number | null>(null)
const hoveredIntradayIndex = ref<number | null>(null)
const tooltipPosition = ref({ left: 0, top: 0 })

const routeCode = computed(() => {
  const raw = route.query.code
  return typeof raw === 'string' && raw ? raw : null
})

const entryCards = computed<SharedFundCard[]>(() => {
  return getAnalysisEntryCards(routeCode.value, sharedCards.value, displaySettings.cardCount)
})

const activeCode = computed(() => routeCode.value)
const activeAnalysis = computed(() => (activeCode.value ? getAnalysisMockByCode(activeCode.value) : null))
const candidates = computed(() => searchAnalysisCandidates(keyword.value))
const activePeriod = computed(() => activeAnalysis.value?.periods[activePeriodKey.value] ?? null)
const isIntradayChart = computed(() => activePeriodKey.value === 'intraday')
const showEntryStrip = computed(() => !routeCode.value && entryCards.value.length > 0)
const periodOptions = computed(() => {
  if (!activeAnalysis.value) {
    return []
  }

  return ANALYSIS_PERIOD_KEYS.map((key) => ({
    key,
    optionLabel: getPeriodDisplayLabel(key, activeAnalysis.value?.periods[key].label),
  }))
})
const activePeriodChartLabel = computed(() => getPeriodDisplayLabel(activePeriodKey.value, activePeriod.value?.label))
const chartTitle = computed(() => {
  const shapeLabel = isIntradayChart.value ? '均价 / 成交量 Mock 图' : 'K 线 / 趋势 / 成交量 Mock 图'
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

  const activeMetrics = activePeriod.value.metrics
  const placeholders = Array.from({ length: Math.max(4 - activeMetrics.length, 0) }, (_, index) => ({
    label: `占位指标 ${index + 1}`,
    value: '--',
    summary: '当前周期 mock 指标待补充',
    tone: 'neutral' as const,
  }))

  return [...activeMetrics, ...placeholders].slice(0, 4)
})

const chartCandles = computed(() => {
  const baseCandles = activePeriod.value?.candles ?? []

  if (baseCandles.length === 0) {
    return []
  }

  const priceValues = baseCandles.flat()
  const minPrice = Math.min(...priceValues)
  const maxPrice = Math.max(...priceValues)
  const totalRange = Math.max(maxPrice - minPrice, 0.01)
  const maxLineHeight = 128
  const maxBodyHeight = 104

  return Array.from({ length: 12 }, (_, index) => {
     const [open, close, low, high] = baseCandles[index % baseCandles.length] ?? [0, 0, 0, 0]
      const label = activePeriod.value?.timeAxis[index % (activePeriod.value?.timeAxis.length || 1)] ?? ''
      const priceRange = Math.max(high - low, 0.01)
      const bodyRange = Math.max(Math.abs(close - open), priceRange * 0.35)
      const lineHeight = Math.max(Math.round((priceRange / totalRange) * maxLineHeight), 28)
      const bodyHeight = Math.min(Math.max(Math.round((bodyRange / totalRange) * maxBodyHeight), 18), lineHeight)

      return {
        label,
        open,
        close,
        low,
        high,
        direction: close >= open ? ('bullish' as const) : ('bearish' as const),
        lineHeight,
        bodyHeight,
      }
    })
})

const hoveredCandle = computed(() => {
  if (isIntradayChart.value || hoveredCandleIndex.value === null) {
    return null
  }

  return chartCandles.value[hoveredCandleIndex.value] ?? null
})

const intradayTooltipPoints = computed(() => activePeriod.value?.linePoints ?? [])

const hoveredIntradayPoint = computed(() => {
  if (!isIntradayChart.value || hoveredIntradayIndex.value === null || !activePeriod.value) {
    return null
  }

  return {
    label: activePeriod.value.timeAxis[hoveredIntradayIndex.value] ?? '',
    price: activePeriod.value.linePoints[hoveredIntradayIndex.value] ?? 0,
    average: activePeriod.value.avgLinePoints[hoveredIntradayIndex.value] ?? 0,
  }
})

const hoveredTooltip = computed(() => {
  if (hoveredCandle.value) {
    return {
      type: 'candle' as const,
      ...hoveredCandle.value,
    }
  }

  if (hoveredIntradayPoint.value) {
    return {
      type: 'intraday' as const,
      ...hoveredIntradayPoint.value,
    }
  }

  return null
})

const tooltipStyle = computed(() => ({
  left: `${tooltipPosition.value.left}px`,
  top: `${tooltipPosition.value.top}px`,
}))

const chartVolumes = computed(() => {
  const baseVolumes = activePeriod.value?.volumes ?? []
  const volumes = Array.from({ length: 12 }, (_, index) => baseVolumes[index % baseVolumes.length] ?? 0)
  const maxVolume = Math.max(...volumes, 1)

  return volumes.map((volume) => Math.max(Math.round((volume / maxVolume) * 100), 18))
})

const intradayLinePath = computed(() => buildLinePath(activePeriod.value?.linePoints ?? []))
const intradayAvgLinePath = computed(() => buildLinePath(activePeriod.value?.avgLinePoints ?? []))
const intradayLineColor = computed(() => (colorMode.mode === 'cn' ? '#ef4444' : '#16a34a'))
const intradayAvgLineColor = computed(() => (colorMode.mode === 'cn' ? '#22c55e' : '#ef4444'))

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
  hideCandleTooltip()
  keyword.value = ''
  activePeriodKey.value = 'day'
  void router.push({
    name: 'analysis',
    query: { code },
  })
}

function getCandlePalette(direction: MarketDirection) {
  return getDirectionPalette(colorMode.mode, direction)
}

function getMetricPalette(direction: MarketDirection) {
  return getDirectionPalette(colorMode.mode, direction)
}

function getPeriodDisplayLabel(key: AnalysisPeriodKey, fallbackLabel?: string) {
  const labelMap: Record<AnalysisPeriodKey, string> = {
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

function showCandleTooltip(index: number, event: MouseEvent) {
  hoveredCandleIndex.value = index
  hoveredIntradayIndex.value = null
  updateTooltipPosition(event)
}

function showIntradayTooltip(index: number, event: MouseEvent) {
  hoveredIntradayIndex.value = index
  hoveredCandleIndex.value = null
  updateTooltipPosition(event)
}

function updateTooltipPosition(event: MouseEvent) {
  const currentTarget = event.currentTarget instanceof HTMLElement ? event.currentTarget : null
  const host = currentTarget?.closest('[data-test="analysis-chart-hit-area"]')

  if (!(host instanceof HTMLElement)) {
    return
  }

  const rect = host.getBoundingClientRect()
  tooltipPosition.value = {
    left: Math.max(event.clientX - rect.left + 12, 12),
    top: Math.max(event.clientY - rect.top + 12, 12),
  }
}

function hideCandleTooltip() {
  hoveredCandleIndex.value = null
  hoveredIntradayIndex.value = null
}

function formatTooltipPrice(value: number) {
  return value.toFixed(3)
}

function buildLinePath(points: number[]) {
  if (points.length === 0) {
    return ''
  }

  const min = Math.min(...points)
  const max = Math.max(...points)
  const range = max - min || 1

  return points
    .map((point, index) => {
      const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100
      const y = 100 - ((point - min) / range) * 100
      return `${x},${y}`
    })
    .join(' ')
}

watch(routeCode, (code) => {
  hideCandleTooltip()
  activePeriodKey.value = 'day'

  if (code) {
    keyword.value = ''
    return
  }

  keyword.value = ''
})

watch(activePeriodKey, () => {
  hideCandleTooltip()
})

onMounted(async () => {
  displaySettings.hydrate()
  sharedCards.value = await loadSharedFundCards()
})
</script>

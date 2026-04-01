import type { ColorMode } from '../stores/colorMode'

export type MarketDirection = 'bullish' | 'bearish' | 'neutral'

type DirectionPalette = {
  valueClass: string
  softTextClass: string
  dotClass: string
  barClass: string
}

const PALETTES: Record<ColorMode, Record<MarketDirection, DirectionPalette>> = {
  cn: {
    bullish: {
      valueClass: 'text-red-500',
      softTextClass: 'text-red-400',
      dotClass: 'bg-red-500',
      barClass: 'bg-red-500',
    },
    bearish: {
      valueClass: 'text-green-600',
      softTextClass: 'text-green-500',
      dotClass: 'bg-green-500',
      barClass: 'bg-green-500',
    },
    neutral: {
      valueClass: 'text-gray-500',
      softTextClass: 'text-gray-400',
      dotClass: 'bg-gray-400',
      barClass: 'bg-gray-400',
    },
  },
  intl: {
    bullish: {
      valueClass: 'text-green-600',
      softTextClass: 'text-green-500',
      dotClass: 'bg-green-500',
      barClass: 'bg-green-500',
    },
    bearish: {
      valueClass: 'text-red-500',
      softTextClass: 'text-red-400',
      dotClass: 'bg-red-500',
      barClass: 'bg-red-500',
    },
    neutral: {
      valueClass: 'text-gray-500',
      softTextClass: 'text-gray-400',
      dotClass: 'bg-gray-400',
      barClass: 'bg-gray-400',
    },
  },
}

export function getDirectionPalette(mode: ColorMode, direction: MarketDirection) {
  return { ...PALETTES[mode][direction] }
}

export function numericToDirection(value: number): MarketDirection {
  if (value > 0) {
    return 'bullish'
  }

  if (value < 0) {
    return 'bearish'
  }

  return 'neutral'
}

export function scoreToDirection(score: number): MarketDirection {
  if (score >= 7) {
    return 'bullish'
  }

  if (score >= 4) {
    return 'neutral'
  }

  return 'bearish'
}

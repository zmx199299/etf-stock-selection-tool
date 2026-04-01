import type { ColorMode } from '../stores/colorMode'

export type MarketDirection = 'bullish' | 'bearish' | 'neutral'

type DirectionPalette = {
  valueClass: string
  accentClass: string
}

const PALETTES: Record<ColorMode, Record<MarketDirection, DirectionPalette>> = {
  cn: {
    bullish: {
      valueClass: 'text-red-500',
      accentClass: 'text-red-400',
    },
    bearish: {
      valueClass: 'text-green-600',
      accentClass: 'text-green-500',
    },
    neutral: {
      valueClass: 'text-gray-500',
      accentClass: 'text-gray-400',
    },
  },
  intl: {
    bullish: {
      valueClass: 'text-green-600',
      accentClass: 'text-green-500',
    },
    bearish: {
      valueClass: 'text-red-500',
      accentClass: 'text-red-400',
    },
    neutral: {
      valueClass: 'text-gray-500',
      accentClass: 'text-gray-400',
    },
  },
}

export function getDirectionPalette(mode: ColorMode, direction: MarketDirection) {
  return PALETTES[mode][direction]
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

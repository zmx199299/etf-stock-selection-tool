import { ref } from 'vue'
import { defineStore } from 'pinia'

export const CARD_COUNT_STORAGE_KEY = 'display-card-count'

const DEFAULT_CARD_COUNT = 10

const VALID_CARD_COUNTS = [6, 8, 10, 12] as const

export type CardCount = (typeof VALID_CARD_COUNTS)[number]

function isValidCardCount(value: number): value is CardCount {
  return (VALID_CARD_COUNTS as readonly number[]).includes(value)
}

export const useDisplaySettingsStore = defineStore('displaySettings', () => {
  const cardCount = ref<CardCount>(DEFAULT_CARD_COUNT)
  const hydrated = ref(false)

  function hydrate() {
    if (hydrated.value) {
      return
    }

    const stored = localStorage.getItem(CARD_COUNT_STORAGE_KEY)
    const parsed = Number(stored)
    cardCount.value = isValidCardCount(parsed) ? parsed : DEFAULT_CARD_COUNT
    hydrated.value = true
  }

  function setCardCount(count: CardCount) {
    cardCount.value = count
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, String(count))
  }

  return {
    cardCount,
    hydrated,
    hydrate,
    setCardCount,
  }
})

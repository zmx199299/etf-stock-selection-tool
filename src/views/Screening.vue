<template>
  <div class="screening">
    <div class="header">
      <h1>形态筛选</h1>
      <div class="filter-controls">
        <select class="select">
          <option>最近30日</option>
          <option>最近60日</option>
        </select>
        <button class="btn-primary">筛选</button>
      </div>
    </div>

    <div class="content">
      <div class="card">
        <div class="card-header">
          <h3>筛选条件</h3>
        </div>
        <div class="filters">
          <div class="filter-item">
            <label>V型反转</label>
            <input type="checkbox" checked />
          </div>
          <div class="filter-item">
            <label>放量突破</label>
            <input type="checkbox" />
          </div>
          <div class="filter-item">
            <label>连续缩量</label>
            <input type="checkbox" />
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>今日结果 (共 {{ results.length }} 只)</h3>
        </div>
        <div class="results">
          <div v-for="item in results" :key="item.code" class="result-card">
            <div class="result-header">
              <span class="code">{{ item.code }}</span>
              <span class="name">{{ item.name }}</span>
            </div>
            <div class="result-body">
              <div class="stat">
                <span class="label">形态</span>
                <span class="value pattern">{{ item.pattern }}</span>
              </div>
              <div class="stat">
                <span class="label">强度</span>
                <span class="value strength">{{ item.strength }}%</span>
              </div>
              <div class="stat">
                <span class="label">现价</span>
                <span class="value">{{ item.price }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const results = ref<any[]>([])
const error = ref<string>('')

const fetchScreeningResults = async () => {
  try {
    error.value = ''
    const { invoke } = await import('@tauri-apps/api/core')
    const res: any = await invoke('invoke_engine', {
      method: 'get_screening_results',
      params: {}
    })
    if (res && Array.isArray(res)) {
      results.value = res
    }
  } catch (e) {
    console.error('Screening failed:', e)
    error.value = e instanceof Error ? e.message : String(e)
    results.value = []
  }
}

onMounted(() => {
  fetchScreeningResults();
})
</script>

<style scoped>
.screening {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.filter-controls {
  display: flex;
  gap: 12px;
}

.select {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: white;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.filters {
  padding: 20px;
  display: flex;
  gap: 24px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
}

.filter-item input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.results {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.result-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.result-card:hover {
  border-color: #2563eb;
  box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
}

.result-header {
  margin-bottom: 12px;
}

.result-header .code {
  font-family: monospace;
  font-weight: 700;
  color: #2563eb;
  margin-right: 8px;
}

.result-header .name {
  font-size: 14px;
  color: #374151;
}

.result-body {
  display: flex;
  justify-content: space-between;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat .label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 2px;
}

.stat .value {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.stat .value.pattern {
  color: #f59e0b;
}

.stat .value.strength {
  color: #22c55e;
}
</style>

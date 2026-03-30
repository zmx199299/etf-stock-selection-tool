<template>
  <div class="scheduler">
    <div class="header">
      <h1>定时任务</h1>
      <button class="btn-primary" @click="handleAddTask">添加任务</button>
    </div>

    <div class="content">
      <div class="card">
        <div class="card-header">
          <h3>已配置任务</h3>
        </div>
        <div class="task-list">
          <div v-for="task in tasks" :key="task.id" class="task-item">
            <div class="task-main">
              <span class="task-name">{{ task.name }}</span>
              <span class="task-cron">{{ task.cron }}</span>
            </div>
            <div class="task-actions">
              <button class="btn-text" @click="handleRun(task.id)">立即执行</button>
              <button class="btn-text danger" @click="handleDelete(task.id)">删除</button>
            </div>
            <div class="task-status">
              <span class="status-dot" :class="task.enabled ? 'active' : ''"></span>
              <span>{{ task.enabled ? '已启用' : '已禁用' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>执行日志</h3>
        </div>
        <div class="log-list">
          <div v-for="log in logs" :key="log.id" class="log-item">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-name">{{ log.taskName }}</span>
            <span class="log-status" :class="log.status.toLowerCase()">{{ log.status }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isDev = import.meta.env.DEV

const mockSchedulerData = {
  tasks: [
    { id: 1, name: '同步基金列表', cron: '每日 00:00', enabled: true },
    { id: 2, name: '初步行情筛选', cron: '每日 15:30', enabled: true },
    { id: 3, name: '净值更新与折溢价计算', cron: '每日 21:00', enabled: true },
  ],
  logs: [
    { id: 1, time: '2026-03-29 21:05:12', taskName: '净值更新与折溢价计算', status: '成功', message: '共更新 512 只基金净值' },
    { id: 2, time: '2026-03-29 15:32:45', taskName: '初步行情筛选', status: '成功', message: '筛选出 34 只形态匹配基金' },
    { id: 3, time: '2026-03-29 00:01:23', taskName: '同步基金列表', status: '成功', message: '列表无变化' },
  ]
}

const tasks = ref<any[]>([])
const logs = ref<any[]>([])

const fetchSchedulerData = async () => {
  try {
    if (isDev) {
      tasks.value = mockSchedulerData.tasks
      logs.value = mockSchedulerData.logs
    } else {
      const { invoke } = await import('@tauri-apps/api/core')
      const res: any = await invoke('invoke_engine', {
        method: 'get_scheduler_data',
        params: {}
      })
      if (res) {
        tasks.value = res.tasks || []
        logs.value = res.logs || []
      }
    }
  } catch (error) {
    console.error('获取定时任务数据失败:', error)
    tasks.value = mockSchedulerData.tasks
    logs.value = mockSchedulerData.logs
  }
}

onMounted(() => {
  fetchSchedulerData();
})

const handleAddTask = () => {
  alert('添加新任务功能开发中...')
}

const handleRun = (id: number) => {
  alert('正在执行任务 ID: ' + id)
}

const handleDelete = (id: number) => {
  if (confirm('确定要删除此任务吗？')) {
    tasks.value = tasks.value.filter(t => t.id !== id)
  }
}
</script>

<style scoped>
.scheduler {
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

.task-list {
  padding: 0 20px;
}

.task-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 16px;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f3f4f6;
}

.task-item:last-child {
  border-bottom: none;
}

.task-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.task-cron {
  font-size: 13px;
  color: #6b7280;
}

.task-actions {
  display: flex;
  gap: 12px;
}

.btn-text {
  background: none;
  border: none;
  color: #2563eb;
  font-size: 13px;
  cursor: pointer;
}

.btn-text.danger {
  color: #ef4444;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #d1d5db;
}

.status-dot.active {
  background: #22c55e;
}

.log-list {
  padding: 0 20px 20px;
}

.log-item {
  display: grid;
  grid-template-columns: 160px 120px 80px 1fr;
  gap: 16px;
  padding: 12px 0;
  font-size: 13px;
  border-bottom: 1px solid #f3f4f6;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #6b7280;
}

.log-name {
  font-weight: 500;
  color: #1f2937;
}

.log-status {
  font-weight: 600;
}

.log-status.成功 {
  color: #22c55e;
}

.log-status.失败 {
  color: #ef4444;
}

.log-message {
  color: #6b7280;
}
</style>

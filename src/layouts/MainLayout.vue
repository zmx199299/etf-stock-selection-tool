<template>
  <div class="flex flex-col md:flex-row min-h-screen text-gray-900">
    <aside class="w-full md:w-64 bg-white border-b md:border-r border-gray-100 md:fixed md:h-screen z-50 flex flex-col">
        <div class="p-8">
            <h1 class="text-xl font-black tracking-tighter text-blue-600 italic">FUNDFLOW</h1>
        </div>
        <nav class="flex md:flex-col px-4 space-y-1">
            <router-link to="/" class="nav-item flex items-center px-4 py-3 rounded-xl font-bold text-sm" :class="$route.path === '/' ? 'active' : 'text-gray-400 hover:bg-gray-50 transition-all font-medium'">📊 今日行情</router-link>
            <router-link to="/funds" class="nav-item flex items-center px-4 py-3 rounded-xl font-medium text-sm transition-all" :class="$route.path === '/funds' ? 'active font-bold' : 'text-gray-400 hover:bg-gray-50'">🔍 全量基金</router-link>
            <router-link to="/analysis" class="nav-item flex items-center px-4 py-3 rounded-xl font-medium text-sm transition-all" :class="$route.path.startsWith('/analysis') ? 'active font-bold' : 'text-gray-400 hover:bg-gray-50'">📈 技术分析</router-link>
            <router-link to="/settings" class="nav-item flex items-center px-4 py-3 rounded-xl font-medium text-sm transition-all md:mt-auto" :class="$route.path === '/settings' ? 'active font-bold' : 'text-gray-400 hover:bg-gray-50'">⚙️ 系统设置</router-link>
        </nav>
    </aside>

    <div class="flex-1 md:ml-64 flex flex-col min-h-screen">
      <RouterView />
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'

const $route = useRoute()
</script>

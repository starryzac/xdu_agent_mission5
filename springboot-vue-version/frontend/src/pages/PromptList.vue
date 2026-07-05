<template>
  <Layout>
    <div class="mb-8 flex items-center justify-between">
      <h2 class="text-2xl font-bold text-balance">提示词列表</h2>
      <router-link to="/prompts/new" class="inline-flex items-center gap-1.5 rounded-lg bg-amber-400 px-4 py-2 text-sm font-semibold text-bg hover:bg-amber-300 transition-all active:scale-[0.97] no-underline">+ 新建提示词</router-link>
    </div>

    <div v-if="error" class="mb-6 rounded-lg border border-danger-dim bg-danger/5 p-4 text-sm text-danger" role="alert">
      <p>{{ error }}</p>
      <button @click="fetchPrompts" class="mt-2 underline hover:no-underline">重试</button>
    </div>

    <p v-if="loading" class="py-16 text-center text-text-dim">加载中...</p>

    <div v-else-if="prompts.length === 0" class="py-20 text-center animate-slide-up">
      <p class="text-5xl">🧪</p>
      <p class="mt-4 text-lg font-medium text-text-muted">实验室还是空的</p>
      <p class="mt-1 text-sm text-text-dim">创建第一条提示词，开始你的 AI 实验之旅</p>
      <router-link to="/prompts/new" class="btn-primary mt-6 inline-flex items-center gap-1.5 no-underline">+ 创建第一条提示词</router-link>
    </div>

    <div v-else class="grid gap-4 grid-cols-[repeat(auto-fill,minmax(min(100%,420px),1fr))]">
      <div v-for="p in prompts" :key="p.id" class="group relative">
        <PromptCard :prompt="p" />
        <button @click="handleDelete(p.id)" class="absolute right-3 top-3 rounded-md bg-danger/10 px-2 py-1 text-xs text-danger opacity-0 transition-all hover:bg-danger/20 group-hover:opacity-100 focus-visible:opacity-100">删除</button>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/api'
import Layout from '../components/Layout.vue'
import PromptCard from '../components/PromptCard.vue'

const prompts = ref([])
const loading = ref(true)
const error = ref('')

async function fetchPrompts() {
  error.value = ''
  loading.value = true
  try {
    const res = await api.get('/prompts')
    prompts.value = res.data
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function handleDelete(id) {
  if (!window.confirm('确定删除这条提示词吗？')) return
  try {
    await api.del(`/prompts/${id}`)
    prompts.value = prompts.value.filter(p => p.id !== id)
  } catch (err) {
    alert('删除失败: ' + err.message)
  }
}

onMounted(fetchPrompts)
</script>

<template>
  <Layout>
    <div class="mb-6">
      <router-link to="/prompts" class="text-sm text-text-dim hover:text-text-muted no-underline">← 返回列表</router-link>
    </div>

    <div v-if="loading" class="py-16 text-center text-text-dim">加载中...</div>

    <div v-else-if="error" class="rounded-lg border border-danger-dim bg-danger/5 p-8 text-center" role="alert">
      <p class="text-danger">{{ error }}</p>
      <router-link to="/prompts" class="mt-4 inline-block text-amber-400 hover:underline">← 返回列表</router-link>
    </div>

    <div v-else-if="prompt" class="card p-6">
      <!-- Header -->
      <div class="mb-6 flex items-start justify-between gap-4">
        <h2 class="text-2xl font-bold text-balance">{{ prompt.title }}</h2>
        <div class="flex shrink-0 items-center gap-4">
          <span v-if="prompt.rating" class="text-lg">
            <span class="text-amber-400">{{ '★'.repeat(prompt.rating) }}</span><span class="text-zinc-700">{{ '★'.repeat(5 - prompt.rating) }}</span>
          </span>
          <span v-if="prompt.version" class="rounded-md bg-white/[0.04] px-3 py-1 font-mono text-sm text-text-muted">{{ prompt.version }}</span>
        </div>
      </div>

      <!-- Tags -->
      <div v-if="prompt.tags?.length" class="mb-5 flex flex-wrap gap-2">
        <router-link v-for="tag in prompt.tags" :key="tag.id" :to="`/tags/${tag.id}`" class="tag-badge no-underline">{{ tag.title }}</router-link>
      </div>

      <!-- Content -->
      <section class="mb-5">
        <h3 class="mb-2 text-xs font-semibold uppercase tracking-wider text-text-dim">提示词内容</h3>
        <pre class="scrollbar-thin overflow-auto rounded-lg bg-bg px-4 py-3 font-mono text-sm text-text whitespace-pre-wrap">{{ prompt.content }}</pre>
      </section>

      <!-- Notes -->
      <section class="mb-6">
        <h3 class="mb-2 text-xs font-semibold uppercase tracking-wider text-text-dim">反思 & 思路</h3>
        <p class="rounded-lg bg-bg px-4 py-3 text-sm text-text-muted">{{ prompt.notes }}</p>
      </section>

      <!-- Runs -->
      <section class="mb-6">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-text-dim">
            运行记录 <span v-if="prompt.runs?.length" class="ml-2 font-mono text-teal">{{ prompt.runs.length }}</span>
          </h3>
          <button @click="showRunForm = !showRunForm" class="text-xs font-medium text-amber-400 hover:text-amber-300">{{ showRunForm ? '取消' : '+ 新增记录' }}</button>
        </div>

        <form v-if="showRunForm" @submit.prevent="handleAddRun" class="mb-4 grid grid-cols-[2fr_1fr_1fr_auto] gap-3 rounded-lg bg-bg p-4">
          <input v-model="newRun.model" type="text" placeholder="模型名称" required class="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none">
          <input v-model.number="newRun.tokens" type="number" placeholder="Tokens" min="0" class="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none">
          <input v-model.number="newRun.responseTime" type="number" placeholder="耗时 (ms)" min="0" class="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none">
          <button type="submit" class="rounded-md bg-amber-400 px-4 py-2 text-sm font-semibold text-bg hover:bg-amber-300 active:scale-[0.97]">添加</button>
        </form>

        <div v-if="prompt.runs?.length" class="scrollbar-thin overflow-hidden rounded-lg border border-border">
          <table class="w-full text-left text-sm">
            <thead class="bg-bg text-text-dim">
              <tr>
                <th class="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">模型</th>
                <th class="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">Tokens</th>
                <th class="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">耗时</th>
                <th class="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">时间</th>
                <th class="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr v-for="(run, i) in prompt.runs" :key="i" class="text-text-muted hover:bg-white/[0.02]">
                <td class="px-4 py-2.5 font-mono text-xs text-teal">{{ run.model }}</td>
                <td class="px-4 py-2.5 font-mono text-xs">{{ run.tokens?.toLocaleString() }}</td>
                <td class="px-4 py-2.5 font-mono text-xs">{{ run.responseTime }}ms</td>
                <td class="px-4 py-2.5 text-xs text-text-dim">{{ new Date(run.createdAt).toLocaleString('zh-CN') }}</td>
                <td class="px-4 py-2.5"><button @click="handleDeleteRun(i)" class="text-xs text-danger/70 hover:text-danger">删除</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="py-6 text-center text-sm text-text-dim">还没有运行记录 — 点击"+ 新增记录"添加第一次实验</p>
      </section>

      <!-- Timestamps -->
      <div class="mb-6 flex gap-6 text-xs text-text-dim">
        <span>创建于 {{ new Date(prompt.createdAt).toLocaleString('zh-CN') }}</span>
        <span>更新于 {{ new Date(prompt.updatedAt).toLocaleString('zh-CN') }}</span>
      </div>

      <!-- Actions -->
      <div class="flex gap-3 border-t border-border pt-6">
        <router-link :to="`/prompts/${prompt.id}/edit`" class="inline-flex items-center rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 active:scale-[0.97] no-underline">编辑</router-link>
        <button @click="handleDelete" class="inline-flex items-center rounded-lg border border-danger-dim px-5 py-2.5 text-sm font-medium text-danger hover:bg-danger/10">删除</button>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/api'
import Layout from '../components/Layout.vue'

const route = useRoute()
const router = useRouter()
const prompt = ref(null)
const loading = ref(true)
const error = ref('')
const showRunForm = ref(false)
const newRun = ref({ model: '', tokens: 0, responseTime: 0 })

async function fetchPrompt() {
  loading.value = true
  try {
    const res = await api.get(`/prompts/${route.params.id}`)
    prompt.value = res.data
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function handleAddRun() {
  if (!newRun.value.model.trim()) return
  try {
    const runs = [...(prompt.value.runs || []), { ...newRun.value }]
    const res = await api.put(`/prompts/${route.params.id}`, { runs })
    prompt.value = res.data
    showRunForm.value = false
    newRun.value = { model: '', tokens: 0, responseTime: 0 }
  } catch (err) { alert('添加失败: ' + err.message) }
}

async function handleDeleteRun(i) {
  const runs = prompt.value.runs.filter((_, idx) => idx !== i)
  const res = await api.put(`/prompts/${route.params.id}`, { runs })
  prompt.value = res.data
}

async function handleDelete() {
  if (!window.confirm('确定删除这条提示词吗？')) return
  await api.del(`/prompts/${route.params.id}`)
  router.push('/prompts')
}

onMounted(fetchPrompt)
</script>

<style scoped>
.tag-badge {
  display: inline-flex; align-items: center; border: 1px solid rgba(245,158,11,0.2);
  background: rgba(245,158,11,0.05); color: #f59e0b; border-radius: 9999px;
  padding: 0.25rem 0.75rem; font-size: 0.75rem;
}
.tag-badge:hover { border-color: rgba(245,158,11,0.4); background: rgba(245,158,11,0.1); }
</style>

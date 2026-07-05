<template>
  <Layout>
    <div class="mb-6">
      <router-link to="/tags" class="text-sm text-text-dim hover:text-text-muted no-underline">← 返回标签列表</router-link>
    </div>

    <div v-if="loading" class="py-16 text-center text-text-dim">加载中...</div>

    <div v-else-if="error" class="rounded-lg border border-danger-dim bg-danger/5 p-8 text-center" role="alert">
      <p class="text-danger">{{ error }}</p>
      <router-link to="/tags" class="mt-4 inline-block text-amber-400 hover:underline">← 返回标签列表</router-link>
    </div>

    <template v-else-if="tag">
      <div class="card mb-8 p-6">
        <div class="mb-4 flex items-start justify-between gap-4">
          <div class="flex items-center gap-3">
            <span class="rounded-full border border-amber-400/20 bg-amber-400/5 px-4 py-1.5 text-lg font-semibold text-amber-400">{{ tag.title }}</span>
            <span class="text-xs text-text-dim">创建于 {{ new Date(tag.createdAt).toLocaleString('zh-CN') }}</span>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <button @click="editing = !editing; editNotes = tag.notes" class="rounded-lg px-3 py-1.5 text-sm font-medium text-text-dim hover:text-text">{{ editing ? '取消编辑' : '编辑 notes' }}</button>
            <button @click="handleDelete" class="rounded-lg px-3 py-1.5 text-sm font-medium text-danger/70 hover:text-danger">删除</button>
          </div>
        </div>

        <div v-if="editing" class="flex gap-2">
          <textarea v-model="editNotes" rows="2" class="flex-1 resize-y rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20 scrollbar-thin"></textarea>
          <button @click="handleSaveNotes" class="self-end rounded-lg bg-amber-400 px-4 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 active:scale-[0.97]">保存</button>
        </div>
        <p v-else class="rounded-lg bg-bg px-4 py-3 text-sm text-text-muted">{{ tag.notes }}</p>
      </div>

      <h3 class="mb-4 text-lg font-semibold">
        该标签下的提示词
        <span v-if="prompts.length" class="ml-2 font-mono text-sm text-teal">{{ prompts.length }}</span>
      </h3>

      <div v-if="prompts.length === 0" class="py-16 text-center animate-slide-up">
        <p class="text-text-muted">该标签下还没有提示词</p>
        <router-link to="/prompts/new" class="mt-3 inline-flex items-center gap-1.5 text-amber-400 hover:underline no-underline">+ 创建提示词并添加此标签</router-link>
      </div>

      <div v-else class="grid gap-4 grid-cols-[repeat(auto-fill,minmax(min(100%,420px),1fr))]">
        <PromptCard v-for="p in prompts" :key="p.id" :prompt="p" />
      </div>
    </template>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/api'
import Layout from '../components/Layout.vue'
import PromptCard from '../components/PromptCard.vue'

const route = useRoute()
const router = useRouter()
const tag = ref(null)
const prompts = ref([])
const loading = ref(true)
const error = ref('')
const editing = ref(false)
const editNotes = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const [tagRes, promptsRes] = await Promise.all([api.get(`/tags/${route.params.id}`), api.get('/prompts')])
    tag.value = tagRes.data
    editNotes.value = tagRes.data.notes
    prompts.value = promptsRes.data.filter(p => p.tags?.some(t => t.id === tag.value.id))
  } catch (err) { error.value = err.message
  } finally { loading.value = false }
})

async function handleSaveNotes() {
  if (!editNotes.value.trim()) return
  try { const r = await api.put(`/tags/${route.params.id}`, { notes: editNotes.value }); tag.value = r.data; editing.value = false } catch (err) { alert('保存失败: ' + err.message) }
}

async function handleDelete() {
  if (!window.confirm('删除标签不会删除关联的提示词，确定删除？')) return
  await api.del(`/tags/${route.params.id}`)
  router.push('/tags')
}
</script>

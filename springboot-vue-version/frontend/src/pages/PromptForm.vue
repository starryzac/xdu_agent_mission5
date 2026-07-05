<template>
  <div class="min-h-screen bg-bg">
    <div class="mx-auto max-w-2xl px-6 py-8 animate-slide-up">
      <h2 class="mb-8 text-2xl font-bold text-balance">{{ isEdit ? '编辑提示词' : '新建提示词' }}</h2>

      <div v-if="error" class="mb-6 rounded-lg border border-danger-dim bg-danger/5 p-3 text-sm text-danger" role="alert">{{ error }}</div>

      <form @submit.prevent="handleSubmit" class="space-y-5" novalidate>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-text-muted">名称 <span class="text-danger">*</span></label>
          <input v-model="form.title" type="text" maxlength="100" required placeholder="如：通用代码生成器"
                 class="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20">
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-text-muted">提示词内容 <span class="text-danger">*</span></label>
          <textarea v-model="form.content" required rows="8" placeholder="输入完整提示词文本..."
                    class="w-full resize-y rounded-lg border border-border bg-surface px-4 py-2.5 font-mono text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20 scrollbar-thin"></textarea>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-text-muted">反思 & 思路 <span class="text-danger">*</span></label>
          <textarea v-model="form.notes" required rows="3" placeholder="这版为什么有效/失败？思路来源是什么？"
                    class="w-full resize-y rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20 scrollbar-thin"></textarea>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1.5 block text-sm font-medium text-text-muted">版本号</label>
            <input v-model="form.version" type="text" maxlength="50" placeholder="v1 / v2 / ..."
                   class="w-full rounded-lg border border-border bg-surface px-4 py-2.5 font-mono text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20">
          </div>
          <div>
            <fieldset>
              <legend class="mb-1.5 text-sm font-medium text-text-muted">评分</legend>
              <div class="flex items-center gap-1 pt-1">
                <button v-for="star in 5" :key="star" type="button"
                        @click="form.rating = form.rating === star ? 0 : star"
                        :class="star <= form.rating ? 'text-amber-400' : 'text-zinc-700 hover:text-zinc-500'"
                        class="text-xl transition-all active:scale-90 rounded">★</button>
                <span v-if="form.rating > 0" class="ml-2 font-mono text-xs text-text-muted">{{ form.rating }}/5</span>
              </div>
            </fieldset>
          </div>
        </div>

        <!-- Tags -->
        <div>
          <div class="mb-1.5 flex items-center justify-between">
            <span class="text-sm font-medium text-text-muted">标签</span>
            <button type="button" @click="showNewTag = !showNewTag" class="text-xs font-medium text-amber-400 hover:text-amber-300">+ 新建标签</button>
          </div>

          <div v-if="showNewTag" class="mb-3 rounded-lg border border-border bg-bg p-3">
            <div class="mb-2 flex gap-2">
              <input v-model="newTag.title" type="text" placeholder="标签名" maxlength="100" class="flex-1 rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none">
              <input v-model="newTag.notes" type="text" placeholder="说明" class="flex-1 rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none">
            </div>
            <div class="flex gap-2">
              <button type="button" @click="handleCreateTag" class="rounded-md bg-amber-400 px-3 py-1 text-xs font-semibold text-bg hover:bg-amber-300 active:scale-[0.97]">创建并添加</button>
              <button type="button" @click="showNewTag = false" class="rounded-md px-3 py-1 text-xs text-text-dim hover:text-text-muted">取消</button>
            </div>
          </div>

          <div class="scrollbar-thin max-h-44 space-y-0.5 overflow-y-auto rounded-lg border border-border bg-surface p-2">
            <p v-if="allTags.length === 0" class="py-3 text-center text-xs text-text-dim">暂无标签</p>
            <label v-for="tag in allTags" :key="tag.id"
                   class="flex cursor-pointer items-center gap-2.5 rounded-md px-3 py-2 text-sm hover:bg-white/[0.04]"
                   :class="form.tags.includes(tag.id) ? 'text-text' : 'text-text-muted'">
              <input type="checkbox" :checked="form.tags.includes(tag.id)" @change="toggleTag(tag.id)" class="accent-amber-400">
              <span class="font-medium">{{ tag.title }}</span>
              <span class="truncate text-xs text-text-dim">— {{ tag.notes }}</span>
            </label>
          </div>

          <div v-if="form.tags.length" class="mt-2 flex flex-wrap gap-1.5">
            <span v-for="tid in form.tags" :key="tid" class="inline-flex items-center gap-1 rounded-full border border-amber-400/20 bg-amber-400/5 px-2.5 py-1 text-xs font-medium text-amber-400">
              {{ allTags.find(t => t.id === tid)?.title }}
              <button type="button" @click="toggleTag(tid)" class="ml-0.5 rounded-full p-0.5 text-amber-400/60 hover:text-amber-400">×</button>
            </span>
          </div>
        </div>

        <div class="flex gap-3 pt-4">
          <button type="submit" :disabled="loading" class="rounded-lg bg-amber-400 px-6 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 disabled:opacity-50 transition-all active:scale-[0.97]">
            {{ loading ? '保存中...' : isEdit ? '保存修改' : '创建提示词' }}
          </button>
          <button type="button" @click="$router.back()" class="rounded-lg border border-border px-6 py-2.5 text-sm font-medium text-text-muted hover:text-text hover:border-border-hover transition-colors">取消</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/api'

const route = useRoute()
const router = useRouter()
const isEdit = Boolean(route.params.id)

const form = reactive({ title: '', content: '', notes: '', version: '', rating: 0, tags: [] })
const allTags = ref([])
const showNewTag = ref(false)
const newTag = reactive({ title: '', notes: '' })
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  try { const r = await api.get('/tags'); allTags.value = r.data } catch {}
  if (!isEdit) return
  try {
    const r = await api.get(`/prompts/${route.params.id}`)
    const p = r.data
    Object.assign(form, {
      title: p.title, content: p.content, notes: p.notes,
      version: p.version || '', rating: p.rating || 0,
      tags: p.tags?.map(t => t.id) || [],
    })
  } catch (err) { error.value = err.message }
})

function toggleTag(id) {
  const idx = form.tags.indexOf(id)
  if (idx >= 0) form.tags.splice(idx, 1)
  else form.tags.push(id)
}

async function handleCreateTag() {
  if (!newTag.title.trim() || !newTag.notes.trim()) return
  try {
    const r = await api.post('/tags', { ...newTag })
    allTags.value.push(r.data)
    form.tags.push(r.data.id)
    newTag.title = ''; newTag.notes = ''; showNewTag.value = false
  } catch (err) { alert('创建标签失败: ' + err.message) }
}

async function handleSubmit() {
  error.value = ''; loading.value = true
  try {
    const body = { title: form.title, content: form.content, notes: form.notes, version: form.version || undefined, rating: form.rating || undefined, tags: form.tags }
    isEdit ? await api.put(`/prompts/${route.params.id}`, body) : await api.post('/prompts', body)
    router.push('/prompts')
  } catch (err) { error.value = err.message
  } finally { loading.value = false }
}
</script>

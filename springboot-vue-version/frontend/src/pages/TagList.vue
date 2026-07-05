<template>
  <Layout>
    <h2 class="mb-8 text-2xl font-bold text-balance">标签管理</h2>

    <form @submit.prevent="handleCreate" class="mb-8 rounded-xl card p-5">
      <h3 class="mb-3 text-sm font-medium text-text-muted">新建标签</h3>
      <div class="flex gap-3">
        <input v-model="newTag.title" type="text" placeholder="标签名称，如「代码生成」" maxlength="100" required class="flex-1 rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20">
        <input v-model="newTag.notes" type="text" placeholder="说明：用途、适用场景" required class="flex-[2] rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20">
        <button type="submit" :disabled="creating" class="rounded-lg bg-amber-400 px-6 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 disabled:opacity-50 transition-all active:scale-[0.97]">{{ creating ? '创建中...' : '创建' }}</button>
      </div>
    </form>

    <div v-if="error" class="mb-6 rounded-lg border border-danger-dim bg-danger/5 p-4 text-sm text-danger" role="alert">
      <p>{{ error }}</p><button @click="fetchTags" class="mt-2 underline hover:no-underline">重试</button>
    </div>

    <p v-if="loading" class="py-16 text-center text-text-dim">加载中...</p>

    <div v-else-if="tags.length === 0" class="py-20 text-center animate-slide-up">
      <p class="text-5xl">🏷️</p>
      <p class="mt-4 text-lg font-medium text-text-muted">还没有标签</p>
      <p class="mt-1 text-sm text-text-dim">使用上方表单创建第一个</p>
    </div>

    <div v-else class="space-y-2">
      <div v-for="tag in tags" :key="tag.id" class="card card-hover flex items-center gap-4 p-4">
        <template v-if="editingId === tag.id">
          <input v-model="editForm.title" type="text" maxlength="100" class="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text focus:border-amber-400/50 focus:outline-none">
          <input v-model="editForm.notes" type="text" class="flex-[2] rounded-md border border-border bg-bg px-3 py-2 text-sm text-text focus:border-amber-400/50 focus:outline-none">
          <button @click="handleEdit(tag.id)" class="rounded-md bg-amber-400 px-4 py-2 text-xs font-semibold text-bg hover:bg-amber-300 active:scale-[0.97]">保存</button>
          <button @click="editingId = null" class="rounded-md px-4 py-2 text-xs text-text-dim hover:text-text-muted">取消</button>
        </template>
        <template v-else>
          <router-link :to="`/tags/${tag.id}`" class="flex min-w-0 flex-1 items-center gap-3 no-underline hover:opacity-80">
            <span class="shrink-0 rounded-full border border-amber-400/20 bg-amber-400/5 px-3 py-1 text-sm font-medium text-amber-400">{{ tag.title }}</span>
            <span class="min-w-0 truncate text-sm text-text-muted">{{ tag.notes }}</span>
          </router-link>
          <span class="shrink-0 text-xs text-text-dim">{{ new Date(tag.updatedAt).toLocaleDateString('zh-CN') }}</span>
          <button @click="startEdit(tag)" class="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-text-dim hover:text-text">编辑</button>
          <button @click="handleDelete(tag.id)" class="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-danger/70 hover:text-danger">删除</button>
        </template>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api/api'
import Layout from '../components/Layout.vue'

const tags = ref([])
const loading = ref(true)
const error = ref('')
const newTag = reactive({ title: '', notes: '' })
const creating = ref(false)
const editingId = ref(null)
const editForm = reactive({ title: '', notes: '' })

async function fetchTags() {
  error.value = ''; loading.value = true
  try { const r = await api.get('/tags'); tags.value = r.data } catch (err) { error.value = err.message
  } finally { loading.value = false }
}

async function handleCreate() {
  if (!newTag.title.trim() || !newTag.notes.trim()) return
  creating.value = true
  try { const r = await api.post('/tags', { ...newTag }); tags.value.unshift(r.data); newTag.title = ''; newTag.notes = '' } catch (err) { alert('创建失败: ' + err.message)
  } finally { creating.value = false }
}

async function handleDelete(id) {
  if (!window.confirm('删除标签不会删除关联的提示词，确定删除？')) return
  try { await api.del(`/tags/${id}`); tags.value = tags.value.filter(t => t.id !== id) } catch (err) { alert('删除失败: ' + err.message) }
}

function startEdit(tag) { editingId.value = tag.id; editForm.title = tag.title; editForm.notes = tag.notes }

async function handleEdit(id) {
  if (!editForm.title.trim() || !editForm.notes.trim()) return
  try { const r = await api.put(`/tags/${id}`, { ...editForm }); tags.value = tags.value.map(t => t.id === id ? r.data : t); editingId.value = null } catch (err) { alert('编辑失败: ' + err.message) }
}

onMounted(fetchTags)
</script>

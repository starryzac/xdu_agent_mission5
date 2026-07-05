<template>
  <router-link :to="`/prompts/${prompt.id}`" class="card card-hover group block p-5 no-underline">
    <div class="mb-3 flex items-start justify-between gap-4">
      <h3 class="truncate text-base font-semibold text-text group-hover:text-amber-400 transition-colors">{{ prompt.title }}</h3>
      <div class="flex shrink-0 items-center gap-3 text-sm">
        <span v-if="prompt.rating" class="text-amber-400 font-mono text-xs tracking-wider">
          {{ '★'.repeat(prompt.rating) }}<span class="text-zinc-700">{{ '★'.repeat(5 - prompt.rating) }}</span>
        </span>
        <span v-if="prompt.version" class="rounded-md bg-white/[0.04] px-2 py-0.5 font-mono text-[11px] text-text-muted">{{ prompt.version }}</span>
      </div>
    </div>
    <p class="mb-3 line-clamp-2 text-sm leading-relaxed text-text-muted">{{ prompt.content }}</p>
    <div class="flex flex-wrap items-center gap-2">
      <span v-for="tag in prompt.tags" :key="tag.id" class="tag-badge">{{ tag.title }}</span>
      <span class="ml-auto text-xs text-text-dim">{{ fmtDate(prompt.updatedAt) }}</span>
    </div>
  </router-link>
</template>

<script setup>
defineProps({ prompt: Object })

function fmtDate(s) {
  return new Date(s).toLocaleDateString('zh-CN')
}
</script>

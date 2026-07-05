<template>
  <div class="min-h-screen bg-bg text-text">
    <header class="sticky top-0 z-50 border-b border-border bg-bg/80 backdrop-blur-md">
      <div class="mx-auto flex h-14 max-w-page items-center justify-between px-6">
        <router-link to="/prompts" class="flex items-center gap-2.5 text-text no-underline">
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-400/10 text-base">⚡</span>
          <span class="text-lg font-semibold tracking-tight">Prompt Lab</span>
        </router-link>
        <nav class="flex gap-1">
          <router-link to="/prompts" :class="linkClass('/prompts')">Prompts</router-link>
          <router-link to="/tags" :class="linkClass('/tags')">Tags</router-link>
        </nav>
      </div>
    </header>
    <main class="mx-auto max-w-page px-6 py-8 animate-fade-in">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()

function linkClass(path) {
  const active = route.path.startsWith(path)
  return [
    'relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
    active ? 'text-amber-400 bg-amber-400/10' : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]',
  ].join(' ')
}
</script>

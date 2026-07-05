<template>
  <router-link v-if="!onRemove" :to="`/tags/${tag.id}`" class="tag-badge">{{ tag.title }}</router-link>
  <span v-else class="tag-badge cursor-pointer" @click="onRemove">{{ tag.title }} <span class="ml-0.5 text-amber-400/60 hover:text-amber-400">×</span></span>
</template>

<script setup>
defineProps({ tag: Object, onRemove: Function })
</script>

<style scoped>
.tag-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  border: 1px solid rgba(245,158,11,0.2);
  background: rgba(245,158,11,0.05);
  color: #f59e0b;
  border-radius: 9999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  text-decoration: none;
  transition: border-color 0.15s, background-color 0.15s;
}
.tag-badge:hover {
  border-color: rgba(245,158,11,0.4);
  background: rgba(245,158,11,0.1);
}
</style>

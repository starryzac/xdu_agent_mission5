import { createRouter, createWebHistory } from 'vue-router'
import PromptList from '../pages/PromptList.vue'
import PromptDetail from '../pages/PromptDetail.vue'
import PromptForm from '../pages/PromptForm.vue'
import TagList from '../pages/TagList.vue'
import TagDetail from '../pages/TagDetail.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/prompts' },
    { path: '/prompts', component: PromptList },
    { path: '/prompts/new', component: PromptForm },
    { path: '/prompts/:id', component: PromptDetail },
    { path: '/prompts/:id/edit', component: PromptForm },
    { path: '/tags', component: TagList },
    { path: '/tags/:id', component: TagDetail },
  ],
})

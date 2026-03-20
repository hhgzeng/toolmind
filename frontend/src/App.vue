<script setup lang="ts">
import { theme } from './apis/theme';

// 初始化主题（从 localStorage 恢复，并给根元素打上 theme-light / theme-dark class）
theme()
</script>

<template>
  <router-view></router-view>
</template> 

<style lang="scss" scoped>
</style>

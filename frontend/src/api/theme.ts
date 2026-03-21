import { ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark'

const THEME_STORAGE_KEY = 'toolmind-theme'

const themeRef = ref<ThemeMode>('light')
let initialized = false

const applyThemeClass = (mode: ThemeMode) => {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.classList.remove('theme-light', 'theme-dark')
  root.classList.add(mode === 'dark' ? 'theme-dark' : 'theme-light')
}

const loadInitialTheme = (): ThemeMode => {
  if (typeof window === 'undefined') return 'light'
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') {
    return stored
  }
  return 'light'
}

const initThemeOnce = () => {
  if (initialized) return
  initialized = true
  themeRef.value = loadInitialTheme()
  applyThemeClass(themeRef.value)

  watch(
    themeRef,
    (val) => {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(THEME_STORAGE_KEY, val)
      }
      applyThemeClass(val)
    },
    { immediate: false }
  )
}

export const theme = () => {
  initThemeOnce()

  const setTheme = (mode: ThemeMode) => {
    themeRef.value = mode
  }

  const toggleTheme = () => {
    themeRef.value = themeRef.value === 'light' ? 'dark' : 'light'
  }

  return {
    theme: themeRef,
    setTheme,
    toggleTheme,
  }
}


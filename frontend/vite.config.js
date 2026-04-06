import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // Allow network access
    // 解决内网穿透时的 Host 检查问题
    allowedHosts: true, 
    // 或者针对旧版 Vite 使用:
    // hmr: {
    //     clientPort: 443, // 如果穿透的是 https，通常端口是 443
    // },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})

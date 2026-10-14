import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Distinct port from the sibling RSI gridworld frontend (5173), so both
// demos can run side by side without a clash.
export default defineConfig({
  plugins: [react()],
  server: { port: 5174 },
})

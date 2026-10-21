import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AppProviders } from './app/providers'
import './styles.css'
import './motion.css'
import './cabinet.css'
import './spec.css'

async function bootstrap() {
  if (import.meta.env.VITE_USE_MOCKS === 'true') {
    const { worker } = await import('./api/mocks/browser')
    await worker.start()
  }
  createRoot(document.getElementById('root')!).render(
    <StrictMode><AppProviders><BrowserRouter><App /></BrowserRouter></AppProviders></StrictMode>,
  )
}

void bootstrap()

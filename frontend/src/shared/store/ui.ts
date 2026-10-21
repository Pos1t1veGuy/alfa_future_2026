import { create } from 'zustand'

type UIState = { sidebarOpen: boolean; wizardStep: number; setSidebarOpen: (value: boolean) => void; setWizardStep: (value: number) => void }
export const useUIStore = create<UIState>((set) => ({ sidebarOpen: false, wizardStep: 0, setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }), setWizardStep: (wizardStep) => set({ wizardStep }) }))

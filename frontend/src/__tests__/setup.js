import '@testing-library/jest-dom'

// Mock window.matchMedia requis par Ant Design
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Mock ResizeObserver requis par Recharts / Ant Design
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}

window.scrollTo = () => {}

import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Ensure each test starts from a clean DOM - without this, elements from
// a previous test can remain mounted and produce false "multiple elements
// found" failures in later tests within the same file.
afterEach(() => {
  cleanup()
})

// jsdom does not implement ResizeObserver, which Recharts' ResponsiveContainer
// requires. A minimal stub is enough for components to mount under test.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver
}

import '@testing-library/jest-dom'
import { beforeAll, afterEach, afterAll } from 'vitest'
import { cleanup } from '@testing-library/react'

// Mock DOMPurify for tests
global.DOMPurify = {
  sanitize: (input: string) => input,
  isSupported: true,
} as any

// Cleanup after each test case
afterEach(() => {
  cleanup()
})
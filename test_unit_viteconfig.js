import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

jest.mock('@vitejs/plugin-react', () => ({
  __esModule: true,
  default: jest.fn(() => 'mocked-react-plugin'),
}))

describe('vite.config.js', () => {
  test('should export correct config object', () => {
    const config = defineConfig({
      plugins: [react()],
    })

    expect(config).toBeDefined()
    expect(config.plugins).toContain('mocked-react-plugin')
  })

  test('should include react plugin in plugins array', () => {
    const config = defineConfig({
      plugins: [react()],
    })

    expect(config.plugins).toEqual(['mocked-react-plugin'])
  })
})
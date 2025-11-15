import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

jest.mock('@eslint/js', () => ({
  configs: {
    recommended: { rules: {} }
  }
}))

jest.mock('globals', () => ({
  browser: {}
}))

jest.mock('eslint-plugin-react-hooks', () => ({
  configs: {
    'recommended-latest': { rules: {} }
  }
}))

jest.mock('eslint-plugin-react-refresh', () => ({
  configs: {
    vite: { rules: {} }
  }
}))

jest.mock('eslint/config', () => ({
  defineConfig: jest.fn((config) => config),
  globalIgnores: jest.fn((ignores) => ({ ignores }))
}))

describe('eslint.config.js', () => {
  test('should export a valid config array', async () => {
    const config = await import('./eslint.config.js')
    expect(Array.isArray(config.default)).toBe(true)
  })

  test('should include global ignores', async () => {
    const config = await import('./eslint.config.js')
    expect(config.default[0]).toEqual({ ignores: ['dist'] })
  })

  test('should extend recommended configs', async () => {
    const config = await import('./eslint.config.js')
    const baseConfig = config.default[1]
    expect(baseConfig.extends).toHaveLength(3)
    expect(baseConfig.extends[0]).toBe(js.configs.recommended)
    expect(baseConfig.extends[1]).toBe(reactHooks.configs['recommended-latest'])
    expect(baseConfig.extends[2]).toBe(reactRefresh.configs.vite)
  })

  test('should configure language options correctly', async () => {
    const config = await import('./eslint.config.js')
    const baseConfig = config.default[1]
    expect(baseConfig.languageOptions.ecmaVersion).toBe(2020)
    expect(baseConfig.languageOptions.globals).toBe(globals.browser)
    expect(baseConfig.languageOptions.parserOptions.ecmaVersion).toBe('latest')
    expect(baseConfig.languageOptions.parserOptions.ecmaFeatures.jsx).toBe(true)
    expect(baseConfig.languageOptions.parserOptions.sourceType).toBe('module')
  })

  test('should define custom rules', async () => {
    const config = await import('./eslint.config.js')
    const baseConfig = config.default[1]
    expect(baseConfig.rules['no-unused-vars']).toEqual(['error', { varsIgnorePattern: '^[A-Z_]' }])
  })
})
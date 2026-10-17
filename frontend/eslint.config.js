// ESLint 플랫폼 설정.
// 이 프로젝트는 TypeScript 7(JS 컴파일러 API 없음)을 쓰므로 typescript-eslint 를 쓸 수 없다.
// 대신 Babel 파서로 TS/TSX 를 파싱하고, 타입 관련 검사는 `tsc`(strict, noUnused*)가 맡는다.
import babelParser from '@babel/eslint-parser'
import js from '@eslint/js'
import reactHooks from 'eslint-plugin-react-hooks'
import globals from 'globals'

const tsParser = (isTSX) => ({
  parser: babelParser,
  parserOptions: {
    requireConfigFile: false,
    babelOptions: {
      babelrc: false,
      configFile: false,
      presets: [
        ['@babel/preset-react', { runtime: 'automatic' }],
        ['@babel/preset-typescript', { isTSX, allExtensions: true }],
      ],
    },
  },
})

export default [
  { ignores: ['dist/**', 'dev-dist/**', 'coverage/**', 'node_modules/**'] },
  js.configs.recommended,
  reactHooks.configs.flat.recommended,
  {
    files: ['**/*.ts'],
    languageOptions: { ...tsParser(false), globals: { ...globals.browser } },
  },
  {
    files: ['**/*.tsx'],
    languageOptions: { ...tsParser(true), globals: { ...globals.browser } },
  },
  {
    files: ['**/*.test.{ts,tsx}', 'src/test-setup.ts'],
    languageOptions: { globals: { ...globals.browser, ...globals.vitest } },
  },
  {
    files: ['eslint.config.js', 'vite.config.ts'],
    languageOptions: { globals: { ...globals.node } },
  },
  {
    // 타입 이름·전역은 tsc 가 검사한다(Babel 파서는 타입 정보가 없어 오탐이 난다).
    rules: {
      'no-undef': 'off',
      'no-unused-vars': 'off',
    },
  },
]

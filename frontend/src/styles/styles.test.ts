import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import postcss from 'postcss'

// vite build는 짝이 안 맞는 중괄호 같은 CSS 오류를 조용히 넘기는 경우가 있고, vitest는 CSS를 처리하지 않으므로
// 모든 스타일 파일을 직접 읽어 파싱해 확인한다.
const dir = __dirname
const files = readdirSync(dir).filter((f) => f.endsWith('.css'))
const read = (f: string) => readFileSync(join(dir, f), 'utf8')

describe('스타일 파일', () => {
  it('스타일 파일을 찾았고 내용이 비어 있지 않다', () => {
    expect(files).toEqual(expect.arrayContaining(['tokens.css', 'base.css', 'components.css']))
    for (const f of files) expect(read(f).length).toBeGreaterThan(50)
  })

  it.each(files)('%s 는 CSS 문법 오류가 없다', (file) => {
    expect(() => postcss.parse(read(file), { from: file })).not.toThrow()
  })

  it('사용하는 디자인 토큰(var(--…))은 tokens.css에 모두 정의되어 있다', () => {
    const all = files.map(read).join('\n')
    const tokens = new Set([...read('tokens.css').matchAll(/(--[a-z0-9-]+)\s*:/g)].map((m) => m[1]))
    const used = new Set([...all.matchAll(/var\((--[a-z0-9-]+)/g)].map((m) => m[1]))
    expect(used.size).toBeGreaterThan(20)
    expect([...used].filter((t) => !tokens.has(t))).toEqual([])
  })
})

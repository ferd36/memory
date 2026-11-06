/**
 * Content-Security-Policy conformance for the renderer.
 *
 * index.html declares `default-src 'self'` with no font-src or remote
 * style-src, so anything the stylesheet or markup fetches from another origin
 * is blocked at runtime — silently. index.css used to @import Inter from
 * fonts.googleapis.com, which meant the font never applied and the app made a
 * network request on every launch.
 *
 * These tests check the source stylesheet and, when it exists, the built one:
 * vite leaves a remote @import verbatim in the bundle, so only checking the
 * source would miss a regression introduced through an imported stylesheet.
 */
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'fs'
import path from 'path'

import { PROJECT_ROOT } from '../helpers/index.js'

/** Comments may name a blocked origin while explaining why it is not used. */
const stripComments = text => text.replace(/\/\*[\s\S]*?\*\//g, '')

const indexHtml = fs.readFileSync(path.join(PROJECT_ROOT, 'index.html'), 'utf8')
const css = stripComments(fs.readFileSync(path.join(PROJECT_ROOT, 'src/renderer/index.css'), 'utf8'))

const REMOTE_URL = /url\(\s*['"]?(https?:)?\/\//i

/** Built CSS bundles, if the project has been built. */
function builtStylesheets() {
  const assetsDir = path.join(PROJECT_ROOT, 'dist/assets')
  if (!fs.existsSync(assetsDir)) return []
  return fs.readdirSync(assetsDir)
    .filter(f => f.endsWith('.css'))
    .map(f => path.join(assetsDir, f))
}

describe('the CSP is declared', () => {
  test('index.html restricts default-src to self', () => {
    assert.match(indexHtml, /http-equiv\s*=\s*"Content-Security-Policy"/)
    assert.match(indexHtml, /default-src 'self'/)
  })

  test('style-src does not allow a remote origin', () => {
    const styleSrc = /style-src ([^;"]*)/.exec(indexHtml)?.[1] ?? ''
    assert.equal(REMOTE_URL.test(styleSrc), false)
    assert.equal(/https?:/.test(styleSrc), false)
  })
})

describe('the source stylesheet stays within the CSP', () => {
  test('has no remote @import', () => {
    assert.equal(/@import[^;]*https?:/i.test(css), false)
    assert.equal(/@import[^;]*\/\//.test(css), false)
  })

  test('fetches nothing from another origin', () => {
    assert.equal(REMOTE_URL.test(css), false)
  })

  test('uses a local font stack rather than a webfont', () => {
    assert.match(css, /--font-stack:/)
    assert.match(css, /font-family: var\(--font-stack\)/)
    assert.equal(/fonts\.googleapis\.com|fonts\.gstatic\.com/.test(css), false)
  })
})

describe('the built stylesheet stays within the CSP', () => {
  const sheets = builtStylesheets()
  const skip = sheets.length > 0 ? false : 'no build output — run `npm run build` first'

  test('no bundled stylesheet imports a remote resource', { skip }, () => {
    for (const sheet of sheets) {
      const content = stripComments(fs.readFileSync(sheet, 'utf8'))
      assert.equal(/@import[^;]*https?:/i.test(content), false,
        `${path.basename(sheet)} still has a remote @import`)
      assert.equal(REMOTE_URL.test(content), false,
        `${path.basename(sheet)} still fetches a remote resource`)
    }
  })
})

describe('the renderer markup fetches nothing remote', () => {
  test('no script or link points at another origin', () => {
    assert.equal(/<(script|link)[^>]+(src|href)\s*=\s*["']https?:/i.test(indexHtml), false)
  })
})

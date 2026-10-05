import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, normalizeErrorDetail, setToken } from '../api'

describe('normalizeErrorDetail', () => {
  it('returns a plain string detail unchanged', () => {
    expect(normalizeErrorDetail({ detail: 'No model is currently deployed.' })).toBe(
      'No model is currently deployed.',
    )
  })

  it('turns a 422 validation-error array into a single readable string', () => {
    const body = {
      detail: [
        { loc: ['body', 'email'], msg: 'field required', type: 'missing' },
        { loc: ['body', 'password'], msg: 'string too short', type: 'string_too_short' },
      ],
    }
    expect(normalizeErrorDetail(body)).toBe('email: field required; password: string too short')
  })

  it('drops the leading "body" location segment', () => {
    const body = { detail: [{ loc: ['body', 'dataset_id'], msg: 'field required', type: 'missing' }] }
    expect(normalizeErrorDetail(body)).toBe('dataset_id: field required')
  })

  it('never renders [object Object] - falls back to a readable message for unknown shapes', () => {
    expect(normalizeErrorDetail({})).not.toContain('[object Object]')
    expect(normalizeErrorDetail(null)).not.toContain('[object Object]')
    expect(normalizeErrorDetail(undefined)).toBe('Something went wrong. Please try again.')
  })

  it('falls back when detail array is empty', () => {
    expect(normalizeErrorDetail({ detail: [] })).toBe('Something went wrong. Please try again.')
  })
})

describe('api request error handling (via fetch)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    setToken(null)
  })

  it('normalises a 422 response from a real endpoint call into ApiError.message', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: [{ loc: ['body', 'email'], msg: 'field required', type: 'missing' }],
        }),
        { status: 422, headers: { 'content-type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.auth.login({ email: '', password: '' })).rejects.toMatchObject({
      message: 'email: field required',
      status: 422,
    })
  })

  it('wraps a network failure as a readable ApiError instead of throwing a raw TypeError', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.auth.me()).rejects.toBeInstanceOf(ApiError)
    await expect(api.auth.me()).rejects.toMatchObject({ status: 0 })
  })
})

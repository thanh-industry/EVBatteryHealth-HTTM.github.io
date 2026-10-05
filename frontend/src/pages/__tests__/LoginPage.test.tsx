import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../../lib/auth'
import { LoginPage } from '../LoginPage'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return {
    ...actual,
    api: {
      ...actual.api,
      auth: {
        me: vi.fn().mockRejectedValue(new actual.ApiError('not authenticated', 401)),
        login: vi.fn(),
      },
    },
  }
})

import { api, ApiError } from '../../lib/api'

function renderLoginPage() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/login']}>
        <LoginPage />
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('LoginPage', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows the sign-in form and the three one-click demo accounts', async () => {
    renderLoginPage()
    expect(await screen.findByRole('heading', { name: /ev battery soh console/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /data scientist/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /technician/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ev owner/i })).toBeInTheDocument()
  })

  it('fills the email and password fields when a demo account is clicked', async () => {
    renderLoginPage()
    const user = userEvent.setup()
    await screen.findByRole('heading', { name: /ev battery soh console/i })

    await user.click(screen.getByRole('button', { name: /data scientist/i }))

    expect(screen.getByLabelText('Email')).toHaveValue('scientist@evsoh.io')
    expect(screen.getByLabelText('Password')).toHaveValue('demo1234')
  })

  it('calls the API client with the entered credentials and shows a readable error on failure', async () => {
    vi.mocked(api.auth.login).mockRejectedValueOnce(new ApiError('Invalid email or password.', 401))
    renderLoginPage()
    const user = userEvent.setup()
    await screen.findByRole('heading', { name: /ev battery soh console/i })

    await user.type(screen.getByLabelText('Email'), 'scientist@evsoh.io')
    await user.type(screen.getByLabelText('Password'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(api.auth.login).toHaveBeenCalledWith({ email: 'scientist@evsoh.io', password: 'wrong-password' })
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
  })

  it('never renders [object Object] when the login error is a validation-array shape', async () => {
    vi.mocked(api.auth.login).mockRejectedValueOnce(
      new ApiError('email: field required', 422),
    )
    renderLoginPage()
    const user = userEvent.setup()
    await screen.findByRole('heading', { name: /ev battery soh console/i })

    await user.type(screen.getByLabelText('Email'), 'bad')
    await user.type(screen.getByLabelText('Password'), 'x')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const alert = await screen.findByRole('alert')
    expect(alert.textContent).not.toContain('[object Object]')
  })
})

import { Lock, Mail } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { Button } from '../components/ui/Button'
import { Alert } from '../components/ui/Feedback'
import { Input } from '../components/ui/Field'
import { useAuth } from '../hooks/useAuth'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { toAppError } from '../utils/errors'
import { AuthShell } from './AuthLayout'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function LoginPage() {
  useDocumentTitle('Sign in')
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from || '/dashboard'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const found: Record<string, string> = {}
    if (!EMAIL_PATTERN.test(email)) found.email = 'Enter a valid email address.'
    if (!password) found.password = 'Enter your password.'
    setErrors(found)
    setFormError('')
    if (Object.keys(found).length) return

    setLoading(true)
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (error) {
      const appError = toAppError(error)
      setErrors(appError.fieldErrors)
      setFormError(appError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle={
        <>
          New to RentWise?{' '}
          <Link to="/register" className="font-medium text-brand-700 hover:text-brand-800">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={submit} noValidate className="space-y-5">
        {formError && <Alert tone="error">{formError}</Alert>}
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          leading={<Mail className="h-4 w-4" />}
          required
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          leading={<Lock className="h-4 w-4" />}
          required
        />
        <Button type="submit" size="lg" className="w-full" loading={loading}>
          Sign in
        </Button>
      </form>
    </AuthShell>
  )
}

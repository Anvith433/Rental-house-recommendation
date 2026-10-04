import { Lock, Mail, UserRound } from 'lucide-react'
import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { Button } from '../components/ui/Button'
import { Alert } from '../components/ui/Feedback'
import { Input } from '../components/ui/Field'
import { useAuth } from '../hooks/useAuth'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { useToast } from '../hooks/useToast'
import { toAppError } from '../utils/errors'
import { AuthShell } from './AuthLayout'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

interface FormState {
  name: string
  email: string
  password: string
  confirm: string
}

function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!form.name.trim()) errors.name = 'Tell us your name.'
  if (!EMAIL_PATTERN.test(form.email)) errors.email = 'Enter a valid email address.'
  if (form.password.length < 8) errors.password = 'Use at least 8 characters.'
  else if (/^\d+$/.test(form.password)) errors.password = "Passwords can't be entirely numeric."
  if (form.confirm !== form.password) errors.confirm = "Passwords don't match."
  return errors
}

export function RegisterPage() {
  useDocumentTitle('Create account')
  const { register } = useAuth()
  const { notify } = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState<FormState>({ name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (key: keyof FormState) => (event: ChangeEvent<HTMLInputElement>) =>
    setForm((current) => ({ ...current, [key]: event.target.value }))

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const found = validate(form)
    setErrors(found)
    setFormError('')
    if (Object.keys(found).length) return

    const [first_name, ...rest] = form.name.trim().split(/\s+/)
    setLoading(true)
    try {
      await register({ email: form.email.trim(), password: form.password, first_name, last_name: rest.join(' ') })
      notify('Welcome to RentWise! Your account is ready.', 'success')
      navigate('/recommendations', { replace: true })
    } catch (error) {
      const appError = toAppError(error)
      const fieldErrors = { ...appError.fieldErrors }
      if (fieldErrors.first_name) fieldErrors.name = fieldErrors.first_name
      setErrors(fieldErrors)
      setFormError(appError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-brand-700 hover:text-brand-800">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} noValidate className="space-y-5">
        {formError && <Alert tone="error">{formError}</Alert>}
        <Input label="Full name" autoComplete="name" value={form.name} onChange={update('name')} error={errors.name} leading={<UserRound className="h-4 w-4" />} maxLength={150} />
        <Input label="Email" type="email" autoComplete="email" value={form.email} onChange={update('email')} error={errors.email} leading={<Mail className="h-4 w-4" />} />
        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
          hint="At least 8 characters; avoid common or all-numeric passwords."
          leading={<Lock className="h-4 w-4" />}
        />
        <Input label="Confirm password" type="password" autoComplete="new-password" value={form.confirm} onChange={update('confirm')} error={errors.confirm} leading={<Lock className="h-4 w-4" />} />
        <Button type="submit" size="lg" className="w-full" loading={loading}>
          Create account
        </Button>
      </form>
    </AuthShell>
  )
}

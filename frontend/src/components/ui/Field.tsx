import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

const CONTROL =
  'block w-full rounded-lg border bg-white px-3 text-sm text-slate-900 shadow-sm transition placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-600/30 disabled:bg-slate-100'

function controlClasses(error?: string, extra = '') {
  return `${CONTROL} ${error ? 'border-rose-400 focus:border-rose-500' : 'border-slate-300 focus:border-brand-600'} ${extra}`
}

interface FieldShellProps {
  id: string
  label?: string
  hint?: string
  error?: string
  children: ReactNode
  className?: string
}

function FieldShell({ id, label, hint, error, children, className = '' }: FieldShellProps) {
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      {children}
      {error ? (
        <p id={`${id}-error`} className="mt-1.5 text-xs text-rose-600">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-slate-500">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  hint?: string
  error?: string
  leading?: ReactNode
  containerClassName?: string
}

export function Input({ label, hint, error, leading, containerClassName, className = '', id, ...props }: InputProps) {
  const generated = useId()
  const inputId = id || generated
  return (
    <FieldShell id={inputId} label={label} hint={hint} error={error} className={containerClassName}>
      <div className="relative">
        {leading && (
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">{leading}</span>
        )}
        <input
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
          className={controlClasses(error, `h-10 ${leading ? 'pl-9' : ''} ${className}`)}
          {...props}
        />
      </div>
    </FieldShell>
  )
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  hint?: string
  error?: string
  containerClassName?: string
}

export function Select({ label, hint, error, containerClassName, className = '', id, children, ...props }: SelectProps) {
  const generated = useId()
  const selectId = id || generated
  return (
    <FieldShell id={selectId} label={label} hint={hint} error={error} className={containerClassName}>
      <select
        id={selectId}
        aria-invalid={error ? true : undefined}
        className={controlClasses(error, `h-10 pr-8 ${className}`)}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  )
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  hint?: string
  error?: string
  containerClassName?: string
}

export function Textarea({ label, hint, error, containerClassName, className = '', id, ...props }: TextareaProps) {
  const generated = useId()
  const textareaId = id || generated
  return (
    <FieldShell id={textareaId} label={label} hint={hint} error={error} className={containerClassName}>
      <textarea
        id={textareaId}
        aria-invalid={error ? true : undefined}
        className={controlClasses(error, `py-2 ${className}`)}
        {...props}
      />
    </FieldShell>
  )
}

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: ReactNode
  description?: string
}

export function Checkbox({ label, description, id, className = '', ...props }: CheckboxProps) {
  const generated = useId()
  const checkboxId = id || generated
  return (
    <label htmlFor={checkboxId} className={`flex cursor-pointer items-start gap-3 ${className}`}>
      <input
        id={checkboxId}
        type="checkbox"
        className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-700 accent-brand-700"
        {...props}
      />
      <span>
        <span className="block text-sm font-medium text-slate-700">{label}</span>
        {description && <span className="block text-xs text-slate-500">{description}</span>}
      </span>
    </label>
  )
}

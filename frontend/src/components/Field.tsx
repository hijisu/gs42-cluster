import { useId, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react'

interface CommonProps {
  label: string
  hint?: string
  error?: string
}

type InputFieldProps = CommonProps & InputHTMLAttributes<HTMLInputElement> & { multiline?: false }
type TextareaFieldProps = CommonProps & TextareaHTMLAttributes<HTMLTextAreaElement> & { multiline: true }

export function Field(props: InputFieldProps | TextareaFieldProps) {
  const id = useId()
  const { label, hint, error, multiline, ...rest } = props
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ') || undefined
  const common = { id, className: 'input', 'aria-invalid': error ? true : undefined, 'aria-describedby': describedBy }

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {multiline ? (
        <textarea {...common} {...(rest as TextareaHTMLAttributes<HTMLTextAreaElement>)} />
      ) : (
        <input {...common} {...(rest as InputHTMLAttributes<HTMLInputElement>)} />
      )}
      {hint && (
        <span id={`${id}-hint`} className="hint">
          {hint}
        </span>
      )}
      {error && (
        <span id={`${id}-error`} className="error" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}

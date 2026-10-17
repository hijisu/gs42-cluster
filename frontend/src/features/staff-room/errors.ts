import { ApiError } from '../../lib/api'
import { errorLabel } from './labels'

export function messageFor(error: unknown, fallback: string): string | null {
  if (!error) return null
  if (error instanceof ApiError) return errorLabel[error.code ?? ''] ?? fallback
  return fallback
}

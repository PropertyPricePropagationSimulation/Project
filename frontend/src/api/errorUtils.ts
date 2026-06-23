interface FieldError {
  field: string
  rejectedValue: string
  reason: string
}

export function parseApiError(e: unknown, fallback: string): string {
  const data = (e as any)?.response?.data
  if (!data) return fallback
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    return (data.detail as FieldError[]).map(f => f.reason).join('\n')
  }
  return data.message ?? fallback
}

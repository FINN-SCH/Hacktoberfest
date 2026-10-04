import type { components } from './generated';

export type Schema<K extends keyof components['schemas']> = components['schemas'][K];
export class ApiError extends Error {
  constructor(public status: number, public detail: Schema<'ErrorBody'>) { super(detail.message); }
}
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch('/api' + path, options);
  if (!response.ok) {
    let envelope: Schema<'ErrorEnvelope'> | undefined;
    try { envelope = await response.json(); } catch { /* network proxy may return non-JSON */ }
    throw new ApiError(response.status, envelope?.error ?? {
      code: 'request_failed', message: 'The request failed. Check the connection and try again.', retryable: true,
    });
  }
  return response.json() as Promise<T>;
}
export function post<T>(path: string, data?: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', ...(data === undefined ? {} :
    { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }) });
}
export async function speech(id: number): Promise<Blob> {
  const response = await fetch('/api/turns/' + id + '/speech', { method: 'POST' });
  if (!response.ok) {
    const body: Schema<'ErrorEnvelope'> = await response.json();
    throw new ApiError(response.status, body.error);
  }
  return response.blob();
}
export function message(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}

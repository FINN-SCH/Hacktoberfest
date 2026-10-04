import { afterEach, expect, it, vi } from 'vitest';
import { ApiError, request, post } from './client';
afterEach(() => vi.unstubAllGlobals());
it('preserves stage and turn id on failure and never retries implicitly', async () => {
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: {
    code: 'unavailable', message: 'Analysis failed', stage: 'analysis', retryable: true, turn_id: 7,
  } }), { status: 502 }));
  vi.stubGlobal('fetch', fetch);
  const error = await post('/sessions/1/turns').catch(e => e);
  expect(error).toBeInstanceOf(ApiError);
  if (!(error instanceof ApiError)) throw new Error("Expected API error");
  expect(error.detail).toMatchObject({ stage: 'analysis', turn_id: 7 });
  expect(fetch).toHaveBeenCalledTimes(1);
});
it('handles a non-JSON network proxy error', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Bad gateway', { status: 502 })));
  await expect(request('/profiles')).rejects.toMatchObject({ status: 502, detail: { code: 'request_failed' } });
});

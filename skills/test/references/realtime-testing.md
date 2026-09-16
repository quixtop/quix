# Testing Real-Time Features

Patterns for testing WebSockets, SSE, async generators, and streaming APIs.

---

## WebSocket Testing

### Node.js (Vitest + ws)

(Examples use Vitest globals — `vi.fn()`, `vi.spyOn` — under Jest substitute `jest.fn()` / `jest.spyOn`.)

```typescript
import { WebSocket, WebSocketServer } from 'ws';

describe('WebSocket chat', () => {
  let wss: WebSocketServer;

  beforeEach(() => {
    wss = new WebSocketServer({ port: 0 });  // Random port
    setupChatHandlers(wss);  // Your app's handler
  });

  afterEach(() => wss.close());

  it('broadcasts messages to all clients', async () => {
    const port = (wss.address() as any).port;

    const client1 = new WebSocket(`ws://localhost:${port}`);
    const client2 = new WebSocket(`ws://localhost:${port}`);

    // Wait for both to connect
    await Promise.all([
      new Promise(r => client1.on('open', r)),
      new Promise(r => client2.on('open', r)),
    ]);

    // Collect messages on client2
    const received: string[] = [];
    client2.on('message', (data) => received.push(data.toString()));

    // Send from client1
    client1.send(JSON.stringify({ type: 'chat', text: 'hello' }));

    // Wait for propagation
    await new Promise(r => setTimeout(r, 100));

    expect(received).toContainEqual(
      expect.stringContaining('hello')
    );

    client1.close();
    client2.close();
  });
});
```

### Testing Connection Lifecycle

```typescript
it('handles disconnection gracefully', async () => {
  const client = new WebSocket(`ws://localhost:${port}`);
  await new Promise(r => client.on('open', r));

  // Track server-side cleanup
  const disconnectSpy = vi.fn();
  wss.on('close-client', disconnectSpy);

  client.close(1000, 'normal close');
  await new Promise(r => setTimeout(r, 50));

  expect(disconnectSpy).toHaveBeenCalled();
});
```

---

## Server-Sent Events (SSE) Testing

### Node.js (fetch-based)

```typescript
import { createServer } from 'http';

it('streams events to client', async () => {
  const server = createServer(sseHandler);  // Your SSE endpoint
  await new Promise<void>(r => server.listen(0, r));
  const port = (server.address() as any).port;

  const response = await fetch(`http://localhost:${port}/events`);
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  const events: string[] = [];
  // Read first 3 events
  for (let i = 0; i < 3; i++) {
    const { value } = await reader.read();
    events.push(decoder.decode(value));
  }

  reader.cancel();
  server.close();

  expect(events[0]).toContain('event: connected');
  expect(events[1]).toContain('data:');
});
```

### Python (httpx)

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_sse_stream():
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", "http://localhost:8000/events") as response:
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    events.append(line)
                if len(events) >= 3:
                    break

    assert any("connected" in e for e in events)
```

---

## Async Generator / Iterator Testing

```typescript
// Testing an async generator that yields paginated results
async function* fetchPages(url: string) {
  let page = 1;
  while (true) {
    const res = await fetch(`${url}?page=${page}`);
    const data = await res.json();
    if (data.items.length === 0) return;
    yield data.items;
    page++;
  }
}

it('yields pages until empty', async () => {
  // Mock fetch to return 2 pages then empty
  const mockResponses = [
    { items: [{ id: 1 }] },
    { items: [{ id: 2 }] },
    { items: [] },
  ];
  let callIndex = 0;
  vi.spyOn(global, 'fetch').mockImplementation(() =>
    Promise.resolve(new Response(JSON.stringify(mockResponses[callIndex++])))
  );

  const pages: any[][] = [];
  for await (const page of fetchPages('http://api.test/items')) {
    pages.push(page);
  }

  expect(pages).toHaveLength(2);
  expect(pages[0][0].id).toBe(1);
});
```

---

## Streaming API Response Testing

### Testing Chunked/Streaming HTTP Responses

```typescript
it('streams JSON lines', async () => {
  const response = await fetch('/api/export', {
    headers: { Accept: 'application/x-ndjson' },
  });

  const lines: object[] = [];
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n');
    buffer = parts.pop()!;  // Keep incomplete line in buffer
    for (const part of parts) {
      if (part.trim()) lines.push(JSON.parse(part));
    }
  }

  expect(lines.length).toBeGreaterThan(0);
  expect(lines[0]).toHaveProperty('id');
});
```

---

## Common Pitfalls

| Error | Cause | Solution |
|-------|-------|----------|
| Test hangs | WebSocket/stream never closes | Add timeout + cleanup in `afterEach` |
| Flaky timing | `setTimeout` for message propagation | Use event-based waiting or retry with backoff |
| Port conflicts | Hardcoded ports across test files | Use port 0 (OS assigns random available port) |
| Resource leaks | Server/connections not closed | Always close in `afterEach`, even on failure |

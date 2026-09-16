# Contract Testing

Verifies that services agree on API contracts without requiring all services to run simultaneously.

---

## Consumer-Driven Contracts (Pact)

### Flow

```
1. Consumer writes a "pact" (expected request/response pairs)
2. Pact is shared with provider via a Pact Broker
3. Provider verifies it can fulfill all consumer pacts
4. Breaking changes caught before deployment
```

### Consumer Test (JavaScript + Pact)

```typescript
import { PactV3, MatchersV3 as Matchers } from '@pact-foundation/pact';

const provider = new PactV3({
  consumer: 'OrderService',
  provider: 'UserService',
});

describe('User API contract', () => {
  it('gets user by ID', async () => {
    provider
      .given('user 123 exists')
      .uponReceiving('a request for user 123')
      .withRequest({ method: 'GET', path: '/users/123' })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: Matchers.string('123'),
          name: Matchers.string('Alice'),
          email: Matchers.email(),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const user = await userClient.getUser('123', mockServer.url);
      expect(user.name).toBeDefined();
      expect(user.email).toContain('@');
    });
  });
});
```

### Provider Verification (JavaScript)

```typescript
import { Verifier } from '@pact-foundation/pact';

describe('UserService provider', () => {
  it('fulfills OrderService contract', async () => {
    await new Verifier({
      providerBaseUrl: 'http://localhost:3000',
      pactBrokerUrl: 'https://pact-broker.company.com',
      provider: 'UserService',
      providerVersion: process.env.GIT_SHA,
      publishVerificationResult: true,
      stateHandlers: {
        'user 123 exists': async () => {
          await db.users.create({ id: '123', name: 'Alice', email: 'alice@test.com' });
        },
      },
    }).verifyProvider();
  });
});
```

### Python (Pact)

```python
import pytest
from pact import Consumer, Provider, Term

@pytest.fixture
def pact():
    pact = Consumer('OrderService').has_pact_with(
        Provider('UserService'),
        pact_dir='./pacts',
    )
    pact.start_service()
    yield pact
    pact.stop_service()

def test_get_user(pact):
    (pact
     .given('user 123 exists')
     .upon_receiving('a request for user 123')
     .with_request('GET', '/users/123')
     .will_respond_with(200, body={
         'id': '123',
         'name': Term(r'.+', 'Alice'),
     }))

    with pact:
        result = user_client.get_user('123', pact.uri)
        assert result['name'] == 'Alice'
```

---

## Spring Cloud Contract (JVM)

For Java/Kotlin microservices using Spring Boot:

```groovy
// contract definition (Groovy DSL)
Contract.make {
    request {
        method 'GET'
        url '/users/123'
    }
    response {
        status 200
        body([
            id: '123',
            name: $(regex('.+')),
            email: $(regex('[^@]+@[^@]+'))
        ])
        headers {
            contentType(applicationJson())
        }
    }
}
```

---

## When to Use Contract Testing

| Signal | Use Contract Tests |
|--------|--------------------|
| Multiple teams own different services | Yes |
| API changes risk breaking consumers | Yes |
| Deployment independence is required | Yes |
| Single team, single deployable | No (integration tests suffice) |
| Unstable/rapidly changing APIs | Wait until API stabilizes |

## Contract vs Integration vs E2E

| Type | Runs All Services | Speed | Confidence |
|------|-------------------|-------|------------|
| Contract | No (mocked) | Fast | Catches schema/format breaks |
| Integration | Some (real deps) | Medium | Catches behavior breaks |
| E2E | Yes (all real) | Slow | Catches deployment/config breaks |

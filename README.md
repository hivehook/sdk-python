# hivehook (Python)

Official Python client for [Hivehook](https://hivehook.com), webhook infrastructure for modern teams (inbound and outbound).

Latest release: **0.1.1** on [PyPI](https://pypi.org/project/hivehook-sdk/).

## Install

```bash
pip install hivehook-sdk
```

For the async client, install the optional extra:

```bash
pip install "hivehook-sdk[async]"
```

## Quick start

```python
import os
from hivehook import HivehookClient

client = HivehookClient(
    base_url="http://localhost:8080",
    api_key=os.environ["HIVEHOOK_API_KEY"],
)

source = client.sources.create(
    name="Stripe production",
    slug="stripe-prod",
    provider_type="stripe",
    verify_config={"secret": "whsec_..."},
)

print(f"created source {source.id}. POST webhooks to /ingest/{source.slug}")
```

## Async usage

```python
from hivehook import AsyncHivehookClient

async with AsyncHivehookClient(api_key="...") as client:
    sources = await client.sources.list()
```

## Webhook signature verification

```python
from hivehook.webhook import verify

signature = request.headers["X-Hivehook-Signature"]
timestamp = int(request.headers["X-Hivehook-Timestamp"])
ok = verify(body, "your-signing-secret", signature, timestamp)
```

## Documentation

See the full reference at [hivehook.com/docs](https://hivehook.com/docs).

## License

MIT. See [LICENSE](LICENSE).

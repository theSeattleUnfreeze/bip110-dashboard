# Regnet Blake2b miner live view

Lean live tip / block list for a **Blake2b + BIP-110 Knots regnet** node (CPU miner → DATUM → Knots). This is separate from the mainnet dual-node BIP-110 fork monitor.

## What it does

- Polls Knots RPC for tip height and recent blocks
- Parses coinbase ASCII and highlights blocks matching `REGNET_COINBASE_TAG`
- Does **not** control mining, speak Stratum, or re-check Blake2b PoW (trusts Knots)

UI: `/regnet` · API: `GET /api/regnet/tip`, `GET /api/regnet/blocks?limit=25`

## Cookie auth (preferred)

Blake2b/regnet Knots typically uses Bitcoin **cookie auth** (`__cookie__:<secret>` in the datadir `.cookie` file), not a long-lived RPC password.

1. Point `BTC_RPC_URL_REGNET` at the Knots RPC (often port **18443** on StartOS — use placeholder host `STARTOS_HOST` in examples).
2. Mount the cookie **read-only** into the API container, e.g.:

```yaml
# docker-compose.yml (illustrative — never commit real paths)
volumes:
  - /path/on/host/to/regnet/.cookie:/run/bitcoin-cookies/regnet/.cookie:ro
```

3. Set:

```bash
REGNET_ENABLED=1
BTC_RPC_URL_REGNET=http://STARTOS_HOST:18443
BTC_RPC_COOKIE_REGNET=/run/bitcoin-cookies/regnet/.cookie
REGNET_COINBASE_TAG=myworker   # substring of DATUM/worker coinbase text
```

Optional fallback if a cookie mount is unavailable: `BTC_RPC_USER_REGNET` / `BTC_RPC_PASSWORD_REGNET`.

On HTTP **401**, the API re-reads the cookie once and retries (node restart regenerates `.cookie`). Failures must not log the secret.

## Epistemic note

Coinbase tags are **voluntary** text. The “yours” badge is a convenience match against `REGNET_COINBASE_TAG`, not cryptographic proof of authorship. Data from your own node is labeled **verifiable** in API payloads.

## Later: self-hosted mempool.space

A full explorer (mempool.space / mempool backend) is **out of scope** for this page. Stock mempool may mishandle v2 / Blake2b headers; regnet has no public explorer. If you self-host later you will still need cookie or rpcuser wiring, plus backend support for the header format — do not assume Blake2b compatibility today.

## Privacy

Never commit `.cookie`, RPC passwords, or real StartOS hostnames/paths. Use placeholders (`STARTOS_HOST`, `/run/bitcoin-cookies/regnet/.cookie`).

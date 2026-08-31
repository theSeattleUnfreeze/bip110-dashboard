# AGENTS.md — bip110-dashboard

Guidance for humans and coding agents working in this repository.

## Anonymity and privacy (read first)

This project monitors **BIP-110**, a contentious Bitcoin consensus proposal. People hold strong views on both sides. **Do not link this work to the maintainer's personal life, employer, or primary GitHub account.**

### Why this matters

- Public association with BIP-110 monitoring can attract harassment, workplace scrutiny, or unwanted attention.
- A single leaked commit email, PR author, or SSH key on the wrong account breaks pseudonymity permanently.
- This repo is published under the **theSeattleUnfreeze** GitHub account only. Personal identity must not appear in commits, PRs, issues, or agent-generated artifacts.

### Required workflow

1. **Before any git write** in this repo (`commit`, `push`, `pr create`):
   ```bash
   github-identity anon
   github-identity check
   ```
2. **Pre-push hook** (machine-local): run once after clone:
   ```bash
   ./scripts/install-local-hooks.sh
   ```
   Pushes are blocked unless `github-identity` reports active profile `anon` and `check` passes.
3. **Never** commit:
   - Personal name or personal email in git metadata
   - Real hostnames, IPs, or `.local` machine names in docs or examples (use placeholders)
   - RPC passwords, `.env` files, or node credentials
   - References to the personal GitHub account (`amcmillion`) or employer

4. **GitHub CLI**: confirm `gh auth status` shows **theSeattleUnfreeze** before `gh pr create`.

5. **SSH clones** use the anon host alias:
   ```bash
   git@github.com-anon:theSeattleUnfreeze/bip110-dashboard.git
   ```

6. **Cursor agent fingerprint** on PRs: use the anon conversation id only; never embed personal account links.

### If something looks wrong

Stop. Run `github-identity check`. Do not push until it passes. Review `git log -1` for author email before every push.

---

## Project overview

Fork and extension of [bip110-observer](https://github.com/decentralizedb/bip110-observer):

- **Backend:** Python Flask (`app/`) — dual-node comparison, signaling, chain metrics
- **Frontend (planned):** Next.js (`web/`) — live dashboard, fork prep advisories, signaling analytics
- **Nodes:** Legacy Bitcoin Core + BIP-110 Knots (Electrum or RPC); self-hosted only

Reference UIs: [orange.surf/live](https://bip110.orange.surf/live.html), [bip110.run](https://bip110.run/).

### Key blocks (BIP-110)

| Height | Event |
|--------|--------|
| 961,632 | Mandatory signaling begins (chains may diverge) |
| 963,648 | Forced lock-in |
| 965,664 | Data rules active |

### Repo layout

| Path | Role |
|------|------|
| `app/` | Flask API and static legacy UI |
| `web/` | Next.js dashboard (Phase 1+) |
| `docker-compose.yml` | API container + data volume |
| `.env.example` | Node RPC / Tor configuration template |

### Local development

```bash
cp .env.example .env   # never commit .env
docker compose up -d --build
curl -s localhost:8110/api/health
```

### Conventions

- Match bip110-observer epistemic tiers: label data as **verifiable**, **estimate**, or **biased sample** in UI.
- Prefer placeholders in examples: `STARTOS_HOST`, `VPS_PUBLIC_IP`, not real infrastructure names.
- Minimize scope per PR; do not mix anonymity tooling changes with feature work unless necessary.
- **English migration:** see [Translate as we go](#translate-as-we-go) below.

---

## Translate as we go

Forked observer code uses Spanish in comments and some API messages. Migrate to English incrementally — no mass-translation PRs.

### New code

- All **comments** in English from the first line (Python, shell, TypeScript, inline comments in HTML/JS).
- New API user-facing strings in English.

### Editing existing code

When you enter a function or change a contiguous block:

1. **Test** — add or extend unit tests that capture **current behavior** before translating.
2. **Translate** — that same block’s comments (and user-facing strings in that block) to English in the same PR.
3. **Update tests** if they asserted Spanish text you translated.

Do not translate untouched files in a feature PR.

### Legacy static UI

`app/static/index.html` and `methodology.html` keep bilingual `en` / `es` user strings until Next.js replaces them or we explicitly drop Spanish. Translate comments when you touch those files; changing `es:` keys requires `test_i18n.py` and `stress.js` updates.

### Checks

```bash
cd app && python3 test_i18n.py && python3 test_pace.py
node stress.js   # when legacy UI/JS changes
```

Cursor rule: `.cursor/rules/translate-as-we-go.mdc`.

---

## Sections to grow

- Electrum + RPC adapter patterns
- Next.js DocsLayout vs DashboardLayout
- API endpoint catalog
- Docker / StartOS node connectivity

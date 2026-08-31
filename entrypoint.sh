#!/bin/sh
set -e

# Start Tor only when needed.
#
# Check all FOUR URLs, not just BTC_RPC_URL. With clearnet/Tor failover the
# .onion usually lives in BTC_RPC_TOR_URL; checking only the first URL left
# Tor stopped and everything failed with "Connection refused" on SOCKS 9050 —
# a message that points nowhere.
NEEDS_TOR=0
for u in "$BTC_RPC_URL" "$BTC_RPC_TOR_URL" "$BTC_RPC_URL_KNOTS" "$BTC_RPC_TOR_URL_KNOTS"; do
  case "$u" in *.onion*) NEEDS_TOR=1 ;; esac
done
[ "$CRAWL_VIA_TOR" = "true" ] && NEEDS_TOR=1

# First .onion among the arguments, or nothing. Avoids repeating the case in
# four places when picking each node's hidden-service URL.
primera_onion() {
  for u in "$@"; do
    case "$u" in *.onion*) echo "$u"; return 0 ;; esac
  done
}

# Probe ONE node via its hidden service.
#   $1 label for logs   $2 url   $3 user   $4 password   $5 attempts
#
# Measures REACHABILITY, not auth: curl treats any HTTP response as success,
# so 401 from bad credentials still counts as "reachable". That is what we
# want here; /api/health reports credential issues once the node is up.
sondear() {
  case "$2" in *.onion*) ;; *) return 0 ;; esac
  n=0
  while [ "$n" -lt "$5" ]; do
    if curl -s --socks5-hostname 127.0.0.1:9050 -m 10 -o /dev/null \
         --user "$3:$4" \
         --data '{"jsonrpc":"1.0","id":"boot","method":"getblockcount","params":[]}' \
         "$2" 2>/dev/null; then
      echo "[bip110] $1: responds via hidden service."
      return 0
    fi
    n=$((n + 1))
    sleep 2
  done
  echo "[bip110] WARNING: $1 does NOT respond via hidden service ($5 attempts)."
  return 1
}

if [ "$NEEDS_TOR" = "1" ]; then
  echo "[bip110] Starting Tor..."

  # Tor in the background, NOT daemonized.
  #
  # Previously we asked for incompatible things: log to stdout and RunAsDaemon,
  # which closes stdout. Tor warned and dropped its log, so on 2026-08-07 the
  # panel missed the secondary node for half an hour and we had to infer the
  # cause with curl — the file that would explain it did not exist. A hidden-
  # service failure is diagnosed from Tor's log or it is not diagnosed.
  #
  # Without RunAsDaemon, Tor inherits the container stdout; messages appear in
  # `docker compose logs` mixed with ours, which is where people look. With
  # exec, Tor is adopted by PID 1 and stays alive as before.
  tor --SocksPort 9050 --Log "notice stdout" &

  # 1. SOCKS must be up before probing anything.
  for i in $(seq 1 60); do
    if python3 -c "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(('127.0.0.1',9050)))" 2>/dev/null; then
      echo "[bip110] Tor SOCKS listening."
      break
    fi
    sleep 2
  done

  # 2. Probe EACH node, not whichever .onion appears first.
  #
  # Previously we took the first .onion among the four variables and stopped.
  # The canonical node is usually first, so boot logged "node responds via
  # hidden service" while the secondary was unreachable. A check that passes
  # without checking what matters is worse than no check: it green-lights the
  # case we need to detect.
  CORE_ONION=$(primera_onion "$BTC_RPC_TOR_URL" "$BTC_RPC_URL")
  KNOTS_ONION=$(primera_onion "$BTC_RPC_TOR_URL_KNOTS" "$BTC_RPC_URL_KNOTS")

  # Canonical node blocks startup: without it there is no dashboard to serve.
  sondear "canonical node" "$CORE_ONION" \
          "$BTC_RPC_USER" "$BTC_RPC_PASSWORD" 60 || true

  # Secondary does NOT block startup — only logs. Missing it is degraded mode
  # (no two-chain comparison), not a reason to refuse boot; the UI and
  # /api/health already say so.
  sondear "secondary node" "$KNOTS_ONION" \
          "${BTC_RPC_USER_KNOTS:-$BTC_RPC_USER}" \
          "${BTC_RPC_PASSWORD_KNOTS:-$BTC_RPC_PASSWORD}" 5 || true
fi

# Exactly ONE worker, on purpose.
#
# Cache and RPC URL pick live in process memory; with two workers each has its
# own copy and the same expensive scan runs twice against the node — minutes
# duplicated over Tor. Work is network-bound, not CPU-bound; threads handle
# concurrent visitors.
exec gunicorn --bind 0.0.0.0:8110 --workers 1 --threads 16 --timeout 900 main:app

import { DocsLayout } from "@/components/layout/DocsLayout";

const advisories = [
  {
    id: "own-your-keys",
    title: "Own your keys",
    body:
      "In a chain split, custodial balances depend on exchange policy. Withdraw to self-custody before mandatory signaling if you want optionality on both chains.",
    steps: [
      "Confirm your wallet can connect to the chain(s) you care about post-split.",
      "Withdraw from exchanges before block 961,632 if you want both-chain optionality.",
      "This is operational risk awareness, not financial or legal advice.",
    ],
  },
  {
    id: "replay-attacks",
    title: "Replay attacks",
    body:
      "After a split, transactions valid on one chain may be replayable on the other because pre-fork UTXO sets match.",
    steps: [
      "Avoid reusing addresses across chains without replay protection.",
      "Use wallets that mark fork IDs or wait for divergent replay protection.",
      "Lightning and custodial services may apply their own policies.",
    ],
  },
  {
    id: "lightning-risks",
    title: "Lightning risks",
    body:
      "Lightning channels tie funds to specific chain rules. A fork can strand or duplicate channel state depending on node and watchtower behavior.",
    steps: [
      "Close or settle channels before contentious periods if you rely on LN.",
      "Assume LN operators may pick one chain only.",
    ],
  },
];

export default function PreparePage() {
  return (
    <DocsLayout>
      <h1 className="text-4xl font-bold">Prepare for a fork</h1>
      <p className="mt-4 text-xl text-muted">
        Guidance for contentious consensus — labeled as guidance, not prediction.
      </p>

      <div className="mt-12 space-y-4">
        {advisories.map((a) => (
          <section
            key={a.id}
            id={a.id}
            className="rounded-xl border border-border bg-card p-6 ring-1 ring-foreground/10"
          >
            <h2 className="text-base font-medium">{a.title}</h2>
            <p className="mt-2 text-muted">{a.body}</p>
            <ol className="mt-4 list-decimal space-y-2 bg-muted/20 rounded-lg p-4 text-sm text-muted">
              {a.steps.map((s) => <li key={s}>{s}</li>)}
            </ol>
          </section>
        ))}
      </div>
    </DocsLayout>
  );
}

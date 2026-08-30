import Link from "next/link";

const links = [
  { href: "/", label: "Live" },
  { href: "/regnet", label: "Regnet" },
  { href: "/prepare", label: "Prepare" },
];

export function SiteHeader() {
  return (
    <header className="fixed top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-semibold text-primary">BIP-110 Dashboard</Link>
        <nav className="flex gap-4 text-sm">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="text-muted hover:text-foreground">
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

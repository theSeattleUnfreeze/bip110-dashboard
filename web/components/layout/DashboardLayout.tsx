import { SiteHeader } from "@/components/SiteHeader";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-6 pb-24 pt-24">{children}</main>
    </div>
  );
}

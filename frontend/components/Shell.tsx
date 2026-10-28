"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { api, token } from "@/lib/api";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/matches", label: "Matches" },
  { href: "/properties", label: "Properties" },
  { href: "/clients", label: "Clients" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/paste", label: "Paste a message" },
  { href: "/import", label: "Import data" },
  { href: "/settings/keys", label: "Integrations & keys", ownerOnly: true },
];

export default function Shell({ title, actions, children }: { title: string; actions?: ReactNode; children: ReactNode }) {
  const router = useRouter();
  const path = usePathname();
  const [me, setMe] = useState<{ full_name: string; role: string } | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!token.get()) { router.replace("/login"); return; }
    api<{ full_name: string; role: string }>("/me").then(setMe).catch(() => {});
  }, [router]);

  if (typeof window !== "undefined" && !token.get()) return null;

  return (
    <div className="min-h-screen lg:flex">
      <header className="flex items-center justify-between border-b border-line bg-white px-4 py-3 lg:hidden">
        <span className="font-semibold text-pine">Shapater</span>
        <button onClick={() => setOpen(!open)} aria-expanded={open} className="rounded border border-line px-3 py-1 text-sm">Menu</button>
      </header>
      <aside className={`${open ? "block" : "hidden"} w-full shrink-0 border-r border-line bg-white lg:block lg:w-60`}>
        <div className="hidden px-5 py-5 text-lg font-semibold text-pine lg:block">Shapater</div>
        <nav className="px-3 pb-4">
          {NAV.filter((n) => !(n as { ownerOnly?: boolean }).ownerOnly || me?.role === "owner").map((n) => {
            const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
            return (
              <Link key={n.href} href={n.href} onClick={() => setOpen(false)} aria-current={active ? "page" : undefined}
                className={`block rounded-md px-3 py-2 text-sm ${active ? "bg-pine-soft font-semibold text-pine" : "text-muted hover:bg-mist hover:text-ink"}`}>
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-line px-5 py-4 text-sm">
          <p className="font-medium">{me?.full_name ?? "…"}</p>
          <p className="text-muted">{me?.role}</p>
          <button onClick={() => { token.clear(); router.replace("/login"); }} className="mt-2 text-muted underline hover:text-ink">Sign out</button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 px-4 py-6 sm:px-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">{title}</h1>
          <div className="flex gap-2">{actions}</div>
        </div>
        {children}
      </main>
    </div>
  );
}

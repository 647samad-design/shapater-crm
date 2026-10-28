"use client";
import { useState } from "react";
import Shell from "@/components/Shell";
import { Button, ErrorNote } from "@/components/ui";
import { api } from "@/lib/api";

type Result = { created: number; duplicates_skipped?: number; errors: { row: number; error: string }[] };

function Uploader({ title, hint, path }: { title: string; hint: string; path: string }) {
  const [res, setRes] = useState<Result | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]; if (!file) return;
    setBusy(true); setErr(null); setRes(null);
    const form = new FormData(); form.append("file", file);
    try { setRes(await api<Result>(path, { form })); } catch (x: any) { setErr(x.message); } finally { setBusy(false); e.target.value = ""; }
  }
  return (
    <section className="rounded-lg border border-line bg-white p-5">
      <h2 className="font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-muted">{hint}</p>
      <label className="mt-4 inline-block"><span className={`inline-block cursor-pointer rounded-md bg-pine px-3.5 py-2 text-sm font-medium text-white hover:bg-pine-dark ${busy ? "opacity-50" : ""}`}>{busy ? "Importing…" : "Choose CSV file"}</span>
        <input type="file" accept=".csv,text/csv" onChange={upload} disabled={busy} className="sr-only" /></label>
      <div className="mt-3 space-y-2"><ErrorNote msg={err} />
        {res && (<div className="text-sm"><p className="font-medium">{res.created} imported{res.duplicates_skipped ? `, ${res.duplicates_skipped} duplicates skipped` : ""}.</p>
          {res.errors.length > 0 && <ul className="mt-1 list-disc pl-5 text-danger">{res.errors.slice(0, 8).map((x) => <li key={x.row}>Row {x.row}: {x.error}</li>)}</ul>}</div>)}
      </div>
    </section>
  );
}

export default function ImportPage() {
  return (
    <Shell title="Import data">
      <p className="mb-5 max-w-2xl text-sm text-muted">Export your register or WhatsApp contacts to Excel, save as CSV, and upload. Column names are detected automatically. Duplicate phone numbers are skipped.</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <Uploader title="Clients" path="/import/clients" hint="Columns: name, phone (or mobile), email, source, notes. Name and phone are required." />
        <Uploader title="Properties" path="/import/properties" hint="Columns: title, purpose, type, price (or demand), currency, beds, city, area, size, unit, owner, permit." />
      </div>
    </Shell>
  );
}

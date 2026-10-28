"use client";
import { useMemo, useState } from "react";
import Shell from "@/components/Shell";
import { Button, Empty, ErrorNote, Field, Modal, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Client, Lead, STAGES } from "@/lib/types";

export default function Pipeline() {
  const leads = useApi<Lead[]>("/leads?limit=500");
  const clients = useApi<Client[]>("/clients?limit=200");
  const [drag, setDrag] = useState<string | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ client_id: "", source: "whatsapp" });
  const names = useMemo(() => Object.fromEntries((clients.data ?? []).map((c) => [c.id, c])), [clients.data]);

  async function move(id: string, stage: string) {
    const prev = leads.data;
    leads.setData((leads.data ?? []).map((l) => (l.id === id ? { ...l, stage } : l)));  // optimistic
    try { await api(`/leads/${id}`, { method: "PATCH", body: { stage } }); }
    catch (e: any) { leads.setData(prev); setErr(e.message); }
  }
  async function create(e: React.FormEvent) {
    e.preventDefault();
    try { await api("/leads", { body: form }); setModal(false); leads.reload(); } catch (e: any) { setErr(e.message); }
  }

  return (
    <Shell title="Pipeline" actions={<Button onClick={() => { setForm({ ...form, client_id: clients.data?.[0]?.id ?? "" }); setModal(true); }}>New lead</Button>}>
      <ErrorNote msg={err || leads.error} />
      {leads.data?.length === 0 && <div className="mb-4"><Empty title="No leads yet" hint="Create a lead from a client to start tracking it through viewing and negotiation. Drag cards between columns as the deal moves." /></div>}
      <div className="flex gap-3 overflow-x-auto pb-4">
        {STAGES.map((st) => {
          const items = (leads.data ?? []).filter((l) => l.stage === st);
          return (
            <section key={st} onDragOver={(e) => { e.preventDefault(); setOver(st); }} onDragLeave={() => setOver(null)}
              onDrop={() => { if (drag) move(drag, st); setDrag(null); setOver(null); }}
              className={`w-64 shrink-0 rounded-lg border p-2 ${over === st ? "border-pine bg-pine-soft" : "border-line bg-white/60"}`} aria-label={`${st} column`}>
              <h2 className="flex justify-between px-2 py-1.5 text-sm font-semibold capitalize"><span>{st}</span><span className="tabular-nums text-muted">{items.length}</span></h2>
              <ul className="min-h-16 space-y-2">
                {items.map((l) => (
                  <li key={l.id} draggable onDragStart={() => setDrag(l.id)} onDragEnd={() => setDrag(null)}
                    className="cursor-grab rounded-md border border-line bg-white p-3 text-sm shadow-sm active:cursor-grabbing">
                    <p className="font-medium">{names[l.client_id]?.name ?? "Client"}</p>
                    <p className="text-xs text-muted">{names[l.client_id]?.phone}{l.source ? ` · ${l.source.replace("_", " ")}` : ""}</p>
                    <label className="mt-2 block text-xs text-muted">Move to
                      <Select value={l.stage} onChange={(e) => move(l.id, e.target.value)} className="mt-0.5 !py-1 text-xs">{STAGES.map((s) => <option key={s}>{s}</option>)}</Select>
                    </label>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
      {modal && (
        <Modal title="New lead" onClose={() => setModal(false)}>
          <form onSubmit={create} className="space-y-3">
            <Field label="Client"><Select required value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })}>{(clients.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name} · {c.phone}</option>)}</Select></Field>
            <Field label="Source"><Select value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}>{["whatsapp", "walk_in", "referral", "zameen", "bayut", "property_finder", "facebook", "website"].map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}</Select></Field>
            <Button type="submit" disabled={!form.client_id}>Create lead</Button>
          </form>
        </Modal>
      )}
    </Shell>
  );
}

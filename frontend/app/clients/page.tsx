"use client";
import Link from "next/link";
import { useState } from "react";
import Shell from "@/components/Shell";
import { Button, Empty, ErrorNote, Field, Input, Modal, Select, Textarea } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Client } from "@/lib/types";

const SOURCES = ["whatsapp", "walk_in", "referral", "zameen", "bayut", "property_finder", "facebook", "website", "other"];
const blankReq = { purpose: "sale", types: "", budget_min: "", budget_max: "", currency: "PKR", city: "", areas: "", beds_min: "", beds_max: "", features: "" };
const list = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

export default function Clients() {
  const [q, setQ] = useState("");
  const { data, error, reload } = useApi<Client[]>(`/clients?limit=100${q ? `&q=${encodeURIComponent(q)}` : ""}`);
  const [addOpen, setAddOpen] = useState(false);
  const [c, setC] = useState({ name: "", phone: "", source: "whatsapp", notes: "" });
  const [err, setErr] = useState<string | null>(null);
  const [reqFor, setReqFor] = useState<Client | null>(null);
  const [r, setR] = useState(blankReq);
  const [found, setFound] = useState<number | null>(null);

  async function addClient(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    try { await api("/clients", { body: c }); setAddOpen(false); setC({ name: "", phone: "", source: "whatsapp", notes: "" }); reload(); }
    catch (e) { setErr(e instanceof ApiError && e.status === 409 ? "This phone number is already in your clients. Search for it instead of adding it again." : (e as Error).message); }
  }

  async function addReq(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    try {
      const created = await api<{ id: string }>("/requirements", { body: {
        client_id: reqFor!.id, purpose: r.purpose, property_types: list(r.types), currency: r.currency,
        budget_min: r.budget_min ? Number(r.budget_min) : null, budget_max: r.budget_max ? Number(r.budget_max) : null,
        city: r.city || null, preferred_areas: list(r.areas), bedrooms_min: r.beds_min ? Number(r.beds_min) : null,
        bedrooms_max: r.beds_max ? Number(r.beds_max) : null, required_features: list(r.features) } });
      const m = await api<unknown[]>(`/matches?requirement_id=${created.id}`);
      setFound(m.length);
    } catch (e: any) { setErr(e.message); }
  }
  const closeReq = () => { setReqFor(null); setFound(null); setR(blankReq); setErr(null); };
  const rs = (k: string) => (e: React.ChangeEvent<any>) => setR({ ...r, [k]: e.target.value });

  return (
    <Shell title="Clients" actions={<Button onClick={() => setAddOpen(true)}>Add client</Button>}>
      <Input aria-label="Search clients" placeholder="Search name or phone" value={q} onChange={(e) => setQ(e.target.value)} className="mb-4 max-w-xs" />
      <ErrorNote msg={error} />
      {data?.length === 0 ? <Empty title="No clients yet" hint="Add a client, then record what they are looking for. Properties that fit show up as matches." action={<Button onClick={() => setAddOpen(true)}>Add client</Button>} /> : (
        <ul className="divide-y divide-line rounded-lg border border-line bg-white">
          {data?.map((cl) => (
            <li key={cl.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div><p className="font-medium">{cl.name}</p><p className="text-sm text-muted">{cl.phone}{cl.source ? ` · ${cl.source.replace("_", " ")}` : ""}</p></div>
              <Button variant="ghost" onClick={() => setReqFor(cl)}>Add requirement</Button>
            </li>
          ))}
        </ul>
      )}

      {addOpen && (
        <Modal title="Add client" onClose={() => setAddOpen(false)}>
          <form onSubmit={addClient} className="space-y-3">
            <Field label="Name"><Input required value={c.name} onChange={(e) => setC({ ...c, name: e.target.value })} /></Field>
            <Field label="Phone / WhatsApp" hint="Any format works: 0300-1234567 or +971 50 123 4567"><Input required value={c.phone} onChange={(e) => setC({ ...c, phone: e.target.value })} /></Field>
            <Field label="Source"><Select value={c.source} onChange={(e) => setC({ ...c, source: e.target.value })}>{SOURCES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}</Select></Field>
            <Field label="Notes"><Textarea rows={2} value={c.notes} onChange={(e) => setC({ ...c, notes: e.target.value })} /></Field>
            <ErrorNote msg={err} /><Button type="submit">Save client</Button>
          </form>
        </Modal>
      )}

      {reqFor && (
        <Modal title={`What is ${reqFor.name} looking for?`} onClose={closeReq}>
          {found !== null ? (
            <div className="space-y-4">
              <p className="text-lg font-semibold">{found > 0 ? `${found} matching ${found === 1 ? "property" : "properties"} found.` : "No matches yet."}</p>
              <p className="text-sm text-muted">{found > 0 ? "They are ready to send on WhatsApp." : "This requirement is saved. New listings that fit will be matched automatically."}</p>
              <div className="flex gap-2">{found > 0 && <Link href="/matches"><Button>View matches</Button></Link>}<Button variant="ghost" onClick={closeReq}>Close</Button></div>
            </div>
          ) : (
            <form onSubmit={addReq} className="grid gap-3 sm:grid-cols-2">
              <Field label="Purpose"><Select value={r.purpose} onChange={rs("purpose")}><option value="sale">Buy</option><option value="rent">Rent</option></Select></Field>
              <Field label="Property types" hint="Comma separated"><Input value={r.types} onChange={rs("types")} placeholder="house, apartment" /></Field>
              <Field label="Budget from"><Input type="number" min="0" value={r.budget_min} onChange={rs("budget_min")} /></Field>
              <Field label="Budget up to"><Input type="number" min="0" value={r.budget_max} onChange={rs("budget_max")} /></Field>
              <Field label="Currency"><Select value={r.currency} onChange={rs("currency")}>{["PKR", "AED", "SAR", "USD"].map((x) => <option key={x}>{x}</option>)}</Select></Field>
              <Field label="City"><Input value={r.city} onChange={rs("city")} /></Field>
              <div className="sm:col-span-2"><Field label="Preferred areas" hint="Comma separated"><Input value={r.areas} onChange={rs("areas")} placeholder="DHA Phase 6, Bahria Town" /></Field></div>
              <Field label="Bedrooms from"><Input type="number" min="0" value={r.beds_min} onChange={rs("beds_min")} /></Field>
              <Field label="Bedrooms up to"><Input type="number" min="0" value={r.beds_max} onChange={rs("beds_max")} /></Field>
              <div className="sm:col-span-2"><Field label="Must have" hint="Comma separated"><Input value={r.features} onChange={rs("features")} placeholder="parking, garden" /></Field></div>
              <div className="space-y-3 sm:col-span-2"><ErrorNote msg={err} /><Button type="submit">Save and find matches</Button></div>
            </form>
          )}
        </Modal>
      )}
    </Shell>
  );
}

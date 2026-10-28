"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Shell from "@/components/Shell";
import { Badge, Button, ErrorNote, Field, Input, Textarea } from "@/components/ui";
import { api } from "@/lib/api";

type Parsed = { kind: "property" | "requirement"; data: Record<string, any>; confidence: number; warnings: string[] };

export default function Paste() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [p, setP] = useState<Parsed | null>(null);
  const [client, setClient] = useState({ name: "", phone: "" });
  const [title, setTitle] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function read() {
    setBusy(true); setErr(null);
    try {
      const r = await api<Parsed>("/ai/parse-message", { body: { text } });
      setP(r);
      setTitle([r.data.area_value && `${r.data.area_value} ${r.data.area_unit}`, r.data.property_type, r.data.area_name].filter(Boolean).join(" ") || "Property");
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }
  const upd = (k: string, v: any) => p && setP({ ...p, data: { ...p.data, [k]: v } });

  async function save() {
    if (!p) return; setErr(null);
    const d = p.data;
    try {
      if (p.kind === "property") {
        await api("/properties", { body: { title, purpose: d.purpose, property_type: d.property_type ?? "house", price: Number(d.price), currency: d.currency ?? "PKR",
          bedrooms: d.bedrooms ?? null, city: d.city, area_name: d.area_name, area_value: d.area_value, area_unit: d.area_unit, country: d.country ?? "PK", features: d.features ?? [] } });
        router.push("/properties");
      } else {
        const cl = await api<{ id: string }>("/clients", { body: { ...client, source: "whatsapp" } });
        await api("/requirements", { body: { client_id: cl.id, purpose: d.purpose, property_types: d.property_types, budget_min: d.budget_min ?? null, budget_max: d.budget_max ?? null,
          currency: d.currency ?? "PKR", city: d.city, preferred_areas: d.preferred_areas, bedrooms_min: d.bedrooms_min, bedrooms_max: d.bedrooms_max, required_features: d.required_features } });
        router.push("/matches");
      }
    } catch (e: any) { setErr(e.message); }
  }

  return (
    <Shell title="Paste a message">
      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <p className="mb-2 text-sm text-muted">Paste a listing or a client request from a WhatsApp group. Shapater reads the price, size, area and type for you to check and save.</p>
          <Textarea rows={7} value={text} onChange={(e) => setText(e.target.value)} placeholder={"5 marla house DHA Phase 6 Lahore, 2.5 crore\nNeed 3 bed apartment in Bahria Town, budget 80 lakh to 1 crore"} aria-label="WhatsApp message" />
          <div className="mt-3"><Button onClick={read} disabled={!text.trim() || busy}>{busy ? "Reading…" : "Read message"}</Button></div>
        </section>
        <section>
          {p && (
            <div className="space-y-4 rounded-lg border border-line bg-white p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">{p.kind === "property" ? "Listing" : "Client requirement"}</h2>
                <Badge tone={p.confidence >= 0.75 ? "pine" : "brass"}>{Math.round(p.confidence * 100)}% understood</Badge>
              </div>
              {p.warnings.length > 0 && <ul className="list-disc pl-5 text-sm text-brass">{p.warnings.map((w) => <li key={w}>{w}</li>)}</ul>}
              {p.kind === "property" ? (<>
                <Field label="Title"><Input value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Price"><Input type="number" value={p.data.price ?? ""} onChange={(e) => upd("price", e.target.value)} /></Field>
                  <Field label="Currency"><Input value={p.data.currency ?? ""} onChange={(e) => upd("currency", e.target.value.toUpperCase())} /></Field>
                  <Field label="Area or society"><Input value={p.data.area_name ?? ""} onChange={(e) => upd("area_name", e.target.value)} /></Field>
                  <Field label="City"><Input value={p.data.city ?? ""} onChange={(e) => upd("city", e.target.value)} /></Field>
                </div>
              </>) : (<>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Client name"><Input required value={client.name} onChange={(e) => setClient({ ...client, name: e.target.value })} /></Field>
                  <Field label="Client phone"><Input required value={client.phone} onChange={(e) => setClient({ ...client, phone: e.target.value })} /></Field>
                  <Field label="Budget from"><Input type="number" value={p.data.budget_min ?? ""} onChange={(e) => upd("budget_min", e.target.value ? Number(e.target.value) : null)} /></Field>
                  <Field label="Budget up to"><Input type="number" value={p.data.budget_max ?? ""} onChange={(e) => upd("budget_max", e.target.value ? Number(e.target.value) : null)} /></Field>
                </div>
                <p className="text-sm text-muted">Looking for {p.data.property_types?.join(", ") || "any type"} in {p.data.preferred_areas?.join(", ") || p.data.city || "any area"}{p.data.bedrooms_min != null ? `, ${p.data.bedrooms_min}${p.data.bedrooms_max !== p.data.bedrooms_min ? `–${p.data.bedrooms_max}` : ""} bedrooms` : ""}.</p>
              </>)}
              <ErrorNote msg={err} />
              <Button onClick={save} disabled={p.kind === "property" ? !p.data.price : !client.name || !client.phone}>{p.kind === "property" ? "Save property" : "Save requirement and find matches"}</Button>
            </div>
          )}
          {!p && <ErrorNote msg={err} />}
        </section>
      </div>
    </Shell>
  );
}

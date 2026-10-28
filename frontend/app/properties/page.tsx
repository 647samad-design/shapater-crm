"use client";
import { useState } from "react";
import Shell from "@/components/Shell";
import { Badge, Button, Empty, ErrorNote, Field, Input, Modal, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { money } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { Property } from "@/lib/types";

const blank = { title: "", purpose: "sale", property_type: "house", price: "", currency: "PKR", bedrooms: "", city: "", area_name: "", area_value: "", area_unit: "marla", permit_number: "" };

export default function Properties() {
  const [q, setQ] = useState("");
  const [purpose, setPurpose] = useState("");
  const qs = `/properties?limit=100${q ? `&q=${encodeURIComponent(q)}` : ""}${purpose ? `&purpose=${purpose}` : ""}`;
  const { data, error, reload } = useApi<Property[]>(qs);
  const [modal, setModal] = useState(false);
  const [f, setF] = useState(blank);
  const [err, setErr] = useState<string | null>(null);
  const set = (k: string) => (e: React.ChangeEvent<any>) => setF({ ...f, [k]: e.target.value });

  async function save(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    try {
      await api("/properties", { body: {
        title: f.title, purpose: f.purpose, property_type: f.property_type, price: Number(f.price), currency: f.currency,
        bedrooms: f.bedrooms ? Number(f.bedrooms) : null, city: f.city || null, area_name: f.area_name || null,
        area_value: f.area_value ? Number(f.area_value) : null, area_unit: f.area_value ? f.area_unit : null,
        permit_number: f.permit_number || null } });
      setModal(false); setF(blank); reload();
    } catch (e: any) { setErr(e.message); }
  }

  return (
    <Shell title="Properties" actions={<Button onClick={() => setModal(true)}>Add property</Button>}>
      <div className="mb-4 flex flex-wrap gap-2">
        <Input aria-label="Search properties" placeholder="Search title, area or address" value={q} onChange={(e) => setQ(e.target.value)} className="max-w-xs" />
        <Select aria-label="Purpose" value={purpose} onChange={(e) => setPurpose(e.target.value)} className="!w-32"><option value="">All</option><option value="sale">For sale</option><option value="rent">For rent</option></Select>
      </div>
      <ErrorNote msg={error} />
      {data?.length === 0 ? <Empty title="No properties yet" hint="Add your first listing, or import your old register from Excel. New listings are matched against client requirements right away." action={<Button onClick={() => setModal(true)}>Add property</Button>} /> : (
        <div className="overflow-x-auto rounded-lg border border-line bg-white">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-line text-muted"><tr>{["Property", "Location", "Size", "Beds", "Price", "Status"].map((h) => <th key={h} className="px-4 py-2.5 font-medium">{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-line">
              {data?.map((p) => (
                <tr key={p.id} className="hover:bg-mist/50">
                  <td className="px-4 py-3"><p className="font-medium">{p.title}</p><p className="text-xs capitalize text-muted">{p.property_type} · for {p.purpose}{p.permit_number ? ` · Permit ${p.permit_number}` : ""}</p></td>
                  <td className="px-4 py-3">{[p.area_name, p.city].filter(Boolean).join(", ") || "–"}</td>
                  <td className="px-4 py-3">{p.area_value ? `${p.area_value} ${p.area_unit}` : "–"}</td>
                  <td className="px-4 py-3 tabular-nums">{p.bedrooms ?? "–"}</td>
                  <td className="px-4 py-3 tabular-nums">{money(p.price, p.currency)}</td>
                  <td className="px-4 py-3"><Badge tone={p.status === "available" ? "pine" : "neutral"}>{p.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {modal && (
        <Modal title="Add property" onClose={() => setModal(false)}>
          <form onSubmit={save} className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2"><Field label="Title"><Input required value={f.title} onChange={set("title")} placeholder="10 Marla house, DHA Phase 6" /></Field></div>
            <Field label="Purpose"><Select value={f.purpose} onChange={set("purpose")}><option value="sale">For sale</option><option value="rent">For rent</option></Select></Field>
            <Field label="Type"><Select value={f.property_type} onChange={set("property_type")}>{["house", "apartment", "villa", "plot", "shop", "office", "penthouse", "townhouse", "portion"].map((t) => <option key={t}>{t}</option>)}</Select></Field>
            <Field label="Price"><Input required type="number" min="1" value={f.price} onChange={set("price")} /></Field>
            <Field label="Currency"><Select value={f.currency} onChange={set("currency")}>{["PKR", "AED", "SAR", "USD"].map((c) => <option key={c}>{c}</option>)}</Select></Field>
            <Field label="City"><Input value={f.city} onChange={set("city")} placeholder="Lahore" /></Field>
            <Field label="Area or society"><Input value={f.area_name} onChange={set("area_name")} placeholder="DHA Phase 6" /></Field>
            <Field label="Size"><Input type="number" min="0" step="any" value={f.area_value} onChange={set("area_value")} /></Field>
            <Field label="Unit"><Select value={f.area_unit} onChange={set("area_unit")}>{["marla", "kanal", "sqft", "sqm", "sqyd"].map((u) => <option key={u}>{u}</option>)}</Select></Field>
            <Field label="Bedrooms"><Input type="number" min="0" value={f.bedrooms} onChange={set("bedrooms")} /></Field>
            <Field label="Permit number" hint="RERA / Trakheesi / REGA, if any"><Input value={f.permit_number} onChange={set("permit_number")} /></Field>
            <div className="space-y-3 sm:col-span-2"><ErrorNote msg={err} /><Button type="submit">Save property</Button></div>
          </form>
        </Modal>
      )}
    </Shell>
  );
}

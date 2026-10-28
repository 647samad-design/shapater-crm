"use client";
import { useState } from "react";
import Shell from "@/components/Shell";
import FitGauge from "@/components/FitGauge";
import { Badge, Button, Empty, ErrorNote, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { money } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { DetailedMatch } from "@/lib/types";

export default function Matches() {
  const [status, setStatus] = useState("new");
  const [minScore, setMinScore] = useState("70");
  const { data, error, loading, reload } = useApi<DetailedMatch[]>(`/matches/detailed?min_score=${minScore}&limit=100${status ? `&status=${status}` : ""}`);
  const [open, setOpen] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function send(m: DetailedMatch) {
    setErr(null);
    try {
      const r = await api<{ wa_link: string }>(`/matches/${m.id}/whatsapp`);
      window.open(r.wa_link, "_blank", "noopener");
      await api(`/matches/${m.id}`, { method: "PATCH", body: { status: "sent" } });
      reload();
    } catch (e: any) { setErr(e.message); }
  }
  async function setSt(m: DetailedMatch, st: string) {
    try { await api(`/matches/${m.id}`, { method: "PATCH", body: { status: st } }); reload(); } catch (e: any) { setErr(e.message); }
  }

  return (
    <Shell title="Matches" actions={<>
      <Select aria-label="Status" value={status} onChange={(e) => setStatus(e.target.value)} className="!w-36">
        <option value="new">To send</option><option value="sent">Sent</option><option value="viewed">Viewed</option><option value="rejected">Rejected</option><option value="">All</option>
      </Select>
      <Select aria-label="Minimum fit" value={minScore} onChange={(e) => setMinScore(e.target.value)} className="!w-36">
        <option value="90">Fit 90+</option><option value="80">Fit 80+</option><option value="70">Fit 70+</option><option value="0">Any fit</option>
      </Select></>}>
      <ErrorNote msg={error || err} />
      {loading && !data && <p className="text-muted">Loading matches…</p>}
      {data?.length === 0 && <Empty title="No matches here" hint="Matches appear automatically when a property fits a client's requirement. Lower the fit filter or add more listings and requirements." />}
      <ul className="space-y-3">
        {data?.map((m) => (
          <li key={m.id} className="rounded-lg border border-line bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold">{m.client.name} <span className="font-normal text-muted">· {m.client.phone}</span></p>
                <p className="text-sm text-muted">Budget up to {m.requirement.budget_max ? money(m.requirement.budget_max, m.requirement.currency) : "open"}{m.requirement.preferred_areas.length ? ` · ${m.requirement.preferred_areas.join(", ")}` : ""}</p>
              </div>
              <div className="text-right text-sm">
                <p className="font-medium">{m.property.title}</p>
                <p className="text-muted">{[m.property.area_name, m.property.city].filter(Boolean).join(", ")} · {money(m.property.price, m.property.currency)}</p>
              </div>
            </div>
            <div className="mt-4"><FitGauge score={m.score} breakdown={m.breakdown} expanded={open === m.id} /></div>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Button onClick={() => send(m)}>Send on WhatsApp</Button>
              <Button variant="ghost" onClick={() => setOpen(open === m.id ? null : m.id)}>{open === m.id ? "Hide details" : "Why this score"}</Button>
              {m.status !== "rejected" && <Button variant="danger" onClick={() => setSt(m, "rejected")}>Not a fit</Button>}
              <span className="ml-auto"><Badge tone={m.status === "new" ? "brass" : "pine"}>{m.status}</Badge></span>
            </div>
          </li>
        ))}
      </ul>
    </Shell>
  );
}

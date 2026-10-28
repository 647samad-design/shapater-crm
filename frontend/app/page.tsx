"use client";
import Link from "next/link";
import Shell from "@/components/Shell";
import FitGauge from "@/components/FitGauge";
import { Empty } from "@/components/ui";
import { useApi } from "@/lib/useApi";
import { money, relDue } from "@/lib/format";
import { Activity, DetailedMatch, STAGES, Summary } from "@/lib/types";

export default function Overview() {
  const s = useApi<Summary>("/dashboard/summary");
  const m = useApi<DetailedMatch[]>("/matches/detailed?status=new&min_score=70&limit=5");
  const due = useApi<Activity[]>("/activities/due");
  const d = s.data;
  const totalLeads = d ? Object.values(d.leads_by_stage).reduce((a, b) => a + b, 0) : 0;
  const figures = d && [
    { label: "New matches to act on", value: d.new_matches, href: "/matches" },
    { label: "Available properties", value: d.properties_available, href: "/properties" },
    { label: "Active requirements", value: d.active_requirements, href: "/clients" },
    { label: "Lead conversion", value: `${d.conversion_rate}%`, href: "/pipeline" },
  ];

  return (
    <Shell title="Overview">
      {s.error && <p className="mb-4 text-danger">{s.error}</p>}
      <div className="grid grid-cols-2 divide-x divide-line rounded-lg border border-line bg-white lg:grid-cols-4">
        {(figures ?? Array(4).fill(null)).map((f, i) => (
          <Link key={i} href={f?.href ?? "#"} className="px-5 py-4 hover:bg-mist/60">
            <p className="text-3xl font-semibold tabular-nums">{f ? f.value : "–"}</p>
            <p className="mt-1 text-sm text-muted">{f?.label ?? "Loading"}</p>
          </Link>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <section className="lg:col-span-3">
          <div className="mb-2 flex items-baseline justify-between">
            <h2 className="font-semibold">Best new matches</h2>
            <Link href="/matches" className="text-sm text-pine underline">See all</Link>
          </div>
          {m.data && m.data.length === 0 && (
            <Empty title="No strong matches yet" hint="Add a client requirement or a property. Matches scoring 70 or more appear here automatically." />
          )}
          <ul className="space-y-3">
            {m.data?.map((x) => (
              <li key={x.id} className="rounded-lg border border-line bg-white p-4">
                <div className="mb-3 flex flex-wrap justify-between gap-2 text-sm">
                  <span><b>{x.client.name}</b> <span className="text-muted">needs</span></span>
                  <span className="text-muted">{x.property.title} · {[x.property.area_name, x.property.city].filter(Boolean).join(", ")} · {money(x.property.price, x.property.currency)}</span>
                </div>
                <FitGauge score={x.score} breakdown={x.breakdown} />
              </li>
            ))}
          </ul>
        </section>

        <div className="space-y-6 lg:col-span-2">
          <section>
            <h2 className="mb-2 font-semibold">Pipeline</h2>
            <div className="rounded-lg border border-line bg-white p-4">
              {totalLeads === 0 ? <p className="text-sm text-muted">No leads yet. Turn a client into a lead from the Pipeline page.</p> : (<>
                <div className="flex h-3 overflow-hidden rounded-sm bg-mist">
                  {STAGES.map((st, i) => d!.leads_by_stage[st] ? (
                    <div key={st} title={`${st}: ${d!.leads_by_stage[st]}`} style={{ flex: d!.leads_by_stage[st], opacity: 0.35 + i * 0.13 }} className={st === "lost" ? "bg-brass" : "bg-pine"} />
                  ) : null)}
                </div>
                <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  {STAGES.map((st) => <li key={st} className="flex justify-between"><span className="capitalize text-muted">{st}</span><span className="tabular-nums">{d!.leads_by_stage[st] ?? 0}</span></li>)}
                </ul>
              </>)}
            </div>
          </section>
          <section>
            <h2 className="mb-2 font-semibold">Follow-ups due</h2>
            <div className="rounded-lg border border-line bg-white">
              {due.data?.length === 0 && <p className="p-4 text-sm text-muted">Nothing due. Schedule a follow-up from any lead.</p>}
              <ul className="divide-y divide-line">
                {due.data?.slice(0, 6).map((a) => (
                  <li key={a.id} className="flex justify-between gap-3 px-4 py-3 text-sm">
                    <span className="capitalize">{a.type.replace("_", " ")}{a.note ? ` · ${a.note}` : ""}</span>
                    <span className="shrink-0 text-brass">{a.due_at && relDue(a.due_at)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
          {d && Object.keys(d.leads_by_source).length > 0 && (
            <section>
              <h2 className="mb-2 font-semibold">Where leads come from</h2>
              <ul className="space-y-2 rounded-lg border border-line bg-white p-4 text-sm">
                {Object.entries(d.leads_by_source).sort((a, b) => b[1] - a[1]).map(([src, n]) => (
                  <li key={src}>
                    <div className="flex justify-between"><span className="capitalize">{src.replace("_", " ")}</span><span className="tabular-nums">{n}</span></div>
                    <div className="mt-1 h-1.5 rounded-sm bg-mist"><div className="h-full rounded-sm bg-pine" style={{ width: `${(n / totalLeads) * 100}%` }} /></div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </Shell>
  );
}

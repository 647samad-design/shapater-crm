"use client";
import { useState } from "react";
import Shell from "@/components/Shell";
import { Badge, Button, ErrorNote, Field, Input, Modal, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { TeamUser } from "@/lib/types";

const ROLE_HELP: Record<string, string> = {
  owner: "Full access, including billing and keys",
  manager: "Sees every client and lead, can assign agents",
  agent: "Sees only the clients and leads assigned to them",
};

export default function Team() {
  const { data, error, reload } = useApi<TeamUser[]>("/users");
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ full_name: "", email: "", password: "", role: "agent" });
  const [err, setErr] = useState<string | null>(null);

  async function add(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    try { await api("/users", { body: f }); setOpen(false); setF({ full_name: "", email: "", password: "", role: "agent" }); reload(); }
    catch (x) { setErr((x as Error).message); }
  }

  return (
    <Shell title="Team" actions={<Button onClick={() => setOpen(true)}>Add team member</Button>}>
      <ErrorNote msg={error} />
      <ul className="divide-y divide-line rounded-lg border border-line bg-white">
        {data?.map((u) => (
          <li key={u.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div><p className="font-medium">{u.full_name}</p><p className="text-sm text-muted">{u.email}</p></div>
            <div className="text-right"><Badge tone={u.role === "owner" ? "brass" : u.role === "manager" ? "pine" : "neutral"}>{u.role}</Badge>
              <p className="mt-1 max-w-56 text-xs text-muted">{ROLE_HELP[u.role]}</p></div>
          </li>
        ))}
      </ul>
      {open && (
        <Modal title="Add team member" onClose={() => setOpen(false)}>
          <form onSubmit={add} className="space-y-3" autoComplete="off">
            <Field label="Full name"><Input required value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} /></Field>
            <Field label="Email"><Input type="email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
            <Field label="Starting password" hint="At least 8 characters. Share it privately; they can use it to sign in."><Input type="password" required minLength={8} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} autoComplete="new-password" /></Field>
            <Field label="Role" hint={ROLE_HELP[f.role]}><Select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option value="agent">Agent</option><option value="manager">Manager</option></Select></Field>
            <ErrorNote msg={err} /><Button type="submit">Add member</Button>
          </form>
        </Modal>
      )}
    </Shell>
  );
}

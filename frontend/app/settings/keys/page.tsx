"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Shell from "@/components/Shell";
import { Badge, Button, Empty, ErrorNote, Field, Input, Modal, Select, Textarea } from "@/components/ui";
import { api, ApiError } from "@/lib/api";

type Key = { id: string; provider: string; label: string; masked: string; notes: string | null; updated_at: string; warning?: string | null };
type Provider = { id: string; name: string; hint: string };

export default function KeysPage() {
  const [keys, setKeys] = useState<Key[] | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [add, setAdd] = useState(false);
  const [edit, setEdit] = useState<Key | null>(null);
  const [del, setDel] = useState<Key | null>(null);
  const [shown, setShown] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const timers = useRef<number[]>([]);
  const pname = (id: string) => providers.find((p) => p.id === id)?.name ?? id;

  const load = useCallback(async () => {
    try {
      const [k, p] = await Promise.all([api<Key[]>("/integrations/keys"), api<Provider[]>("/integrations/providers")]);
      setKeys(k); setProviders(p); setErr(null);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true); else setErr((e as Error).message);
    }
  }, []);
  useEffect(() => { load(); return () => { timers.current.forEach(clearTimeout); }; }, [load]);

  async function reveal(k: Key): Promise<string | null> {
    try { return (await api<{ value: string }>(`/integrations/keys/${k.id}/reveal`, { method: "POST" })).value; }
    catch (e) { setErr((e as Error).message); return null; }
  }
  async function copy(k: Key) {
    const v = await reveal(k);
    if (v === null) return;
    try { await navigator.clipboard.writeText(v); setCopied(k.id); timers.current.push(window.setTimeout(() => setCopied(null), 2000)); }
    catch { setShown((s) => ({ ...s, [k.id]: v })); setErr("Your browser blocked copying. The key is shown below so you can copy it by hand."); }
  }
  async function toggle(k: Key) {
    if (shown[k.id]) { setShown(({ [k.id]: _, ...rest }) => rest); return; }
    const v = await reveal(k);
    if (v === null) return;
    setShown((s) => ({ ...s, [k.id]: v }));
    timers.current.push(window.setTimeout(() => setShown(({ [k.id]: _, ...rest }) => rest), 15000));  // auto-hide
  }
  async function remove() {
    if (!del) return;
    try { await api(`/integrations/keys/${del.id}`, { method: "DELETE" }); setDel(null); load(); } catch (e) { setErr((e as Error).message); setDel(null); }
  }

  if (forbidden) return <Shell title="Integrations & keys"><Empty title="Owners only" hint="Only the agency owner can view or change API keys. Ask your owner to add what you need." /></Shell>;

  return (
    <Shell title="Integrations & keys" actions={<Button onClick={() => setAdd(true)}>Add key</Button>}>
      <p className="mb-5 max-w-2xl text-sm text-muted">Store the keys and tokens your agency uses, such as Stripe or WhatsApp. They are encrypted on the server, only owners can see them, and every copy or change is recorded in the audit log.</p>
      <ErrorNote msg={err} />
      {notice && <p role="status" className="mb-4 rounded-md bg-brass/15 px-3 py-2 text-sm text-brass">{notice}</p>}
      {keys?.length === 0 && <Empty title="No keys yet" hint="Add your Stripe key first if you want to take subscription payments, or a WhatsApp token to send messages from the CRM." action={<Button onClick={() => setAdd(true)}>Add key</Button>} />}
      {keys && keys.length > 0 && (
        <ul className="divide-y divide-line rounded-lg border border-line bg-white">
          {keys.map((k) => (
            <li key={k.id} className="px-4 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="flex flex-wrap items-center gap-2 font-medium"><Badge tone="pine">{pname(k.provider)}</Badge>{k.label}</p>
                  <p className="mt-1.5 break-all font-mono text-sm text-muted" data-testid="key-value">{shown[k.id] ?? k.masked}</p>
                  {k.notes && <p className="mt-1 text-sm text-muted">{k.notes}</p>}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button variant="ghost" onClick={() => copy(k)}>{copied === k.id ? "Copied" : "Copy"}</Button>
                  <Button variant="ghost" onClick={() => toggle(k)}>{shown[k.id] ? "Hide" : "Show"}</Button>
                  <Button variant="ghost" onClick={() => setEdit(k)}>Edit</Button>
                  <Button variant="danger" onClick={() => setDel(k)}>Delete</Button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {add && <KeyForm title="Add key" providers={providers} onClose={() => setAdd(false)} onDone={(w) => { setAdd(false); setNotice(w ?? null); load(); }} />}
      {edit && <KeyForm title={`Edit ${edit.label}`} providers={providers} existing={edit} onClose={() => setEdit(null)} onDone={(w) => { setEdit(null); setNotice(w ?? null); setShown({}); load(); }} />}
      {del && (
        <Modal title="Delete this key?" onClose={() => setDel(null)}>
          <p className="text-sm">“{del.label}” ({pname(del.provider)}) will be removed permanently. Anything that uses it, like payments or WhatsApp sending, will stop working until you add it again.</p>
          <div className="mt-5 flex gap-2"><Button variant="danger" onClick={remove}>Delete key</Button><Button variant="ghost" onClick={() => setDel(null)}>Keep it</Button></div>
        </Modal>
      )}
    </Shell>
  );
}

function KeyForm({ title, providers, existing, onClose, onDone }: { title: string; providers: Provider[]; existing?: Key; onClose: () => void; onDone: (warning?: string | null) => void }) {
  const [f, setF] = useState({ provider: existing?.provider ?? "stripe", label: existing?.label ?? "", value: "", notes: existing?.notes ?? "" });
  const [vis, setVis] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const hint = providers.find((p) => p.id === f.provider)?.hint;

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      const res = existing
        ? await api<Key>(`/integrations/keys/${existing.id}`, { method: "PATCH", body: { label: f.label, notes: f.notes, ...(f.value ? { value: f.value } : {}) } })
        : await api<Key>("/integrations/keys", { body: f });
      onDone(res.warning);
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3" autoComplete="off">
        {!existing && <Field label="Service" hint={hint}><Select value={f.provider} onChange={(e) => setF({ ...f, provider: e.target.value })}>{providers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</Select></Field>}
        <Field label="Label" hint="Helps you tell keys apart, e.g. “Live secret key”"><Input required value={f.label} onChange={(e) => setF({ ...f, label: e.target.value })} /></Field>
        <Field label={existing ? "New key or token" : "Key or token"} hint={existing ? "Leave blank to keep the current value" : undefined}>
          <div className="flex gap-2">
            <Input required={!existing} type={vis ? "text" : "password"} value={f.value} onChange={(e) => setF({ ...f, value: e.target.value })} autoComplete="new-password" spellCheck={false} className="font-mono" />
            <Button type="button" variant="ghost" onClick={() => setVis(!vis)}>{vis ? "Hide" : "Show"}</Button>
          </div>
        </Field>
        <Field label="Notes (optional)"><Textarea rows={2} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field>
        <ErrorNote msg={err} />
        <Button type="submit" disabled={busy}>{busy ? "Saving…" : existing ? "Save changes" : "Save key"}</Button>
      </form>
    </Modal>
  );
}

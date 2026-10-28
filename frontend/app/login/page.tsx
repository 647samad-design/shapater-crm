"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, token } from "@/lib/api";
import { Button, ErrorNote, Field, Input, Select } from "@/components/ui";

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [f, setF] = useState({ agency_name: "", full_name: "", email: "", password: "", country: "PK", currency: "PKR" });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: string) => (e: React.ChangeEvent<any>) => setF({ ...f, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const body = mode === "login" ? { email: f.email, password: f.password } : f;
      const r = await api<{ access_token: string }>(mode === "login" ? "/auth/login" : "/auth/register", { body, auth: false });
      token.set(r.access_token);
      router.replace("/");
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden bg-pine p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <span className="text-lg font-semibold">Shapater</span>
        <div>
          <p className="max-w-md text-4xl font-semibold leading-tight">Every client requirement, matched to the right listing before you open WhatsApp.</p>
          <p className="mt-4 max-w-md text-pine-soft">Built for agencies in Pakistan and the Gulf: marla and sq ft, PKR and AED, one place for leads that used to live in groups and registers.</p>
        </div>
        <span className="text-sm text-pine-soft">Properties · Clients · Matches · Pipeline</span>
      </div>
      <div className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="w-full max-w-sm space-y-4">
          <h1 className="text-2xl font-semibold">{mode === "login" ? "Sign in" : "Create your agency"}</h1>
          {mode === "register" && (<>
            <Field label="Agency name"><Input required value={f.agency_name} onChange={set("agency_name")} /></Field>
            <Field label="Your name"><Input required value={f.full_name} onChange={set("full_name")} /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Country"><Select value={f.country} onChange={set("country")}><option value="PK">Pakistan</option><option value="AE">UAE</option><option value="SA">Saudi Arabia</option></Select></Field>
              <Field label="Currency"><Select value={f.currency} onChange={set("currency")}><option>PKR</option><option>AED</option><option>SAR</option><option>USD</option></Select></Field>
            </div>
          </>)}
          <Field label="Email"><Input type="email" required value={f.email} onChange={set("email")} autoComplete="email" /></Field>
          <Field label="Password" hint={mode === "register" ? "At least 8 characters" : undefined}>
            <Input type="password" required minLength={mode === "register" ? 8 : 1} value={f.password} onChange={set("password")} autoComplete={mode === "login" ? "current-password" : "new-password"} />
          </Field>
          <ErrorNote msg={err} />
          <Button type="submit" disabled={busy} className="w-full">{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create agency"}</Button>
          <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(null); }} className="text-sm text-muted underline">
            {mode === "login" ? "New agency? Create an account" : "Already registered? Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

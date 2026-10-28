/** South-Asian style (Lakh/Crore) for PKR, compact international style for others. */
export function money(amount: number, currency: string): string {
  if (currency === "PKR") {
    if (amount >= 1e7) return `PKR ${trim(amount / 1e7)} Cr`;
    if (amount >= 1e5) return `PKR ${trim(amount / 1e5)} Lakh`;
    return `PKR ${amount.toLocaleString("en-US")}`;
  }
  return `${currency} ${new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 2 }).format(amount)}`;
}
const trim = (n: number) => String(Math.round(n * 100) / 100);

export function relDue(iso: string): string {
  const diff = new Date(iso).getTime() - Date.now();
  const h = Math.round(Math.abs(diff) / 36e5);
  const d = Math.round(h / 24);
  const span = h < 24 ? `${h}h` : `${d}d`;
  return diff < 0 ? `${span} overdue` : `in ${span}`;
}

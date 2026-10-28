import { Breakdown } from "@/lib/types";

const ORDER = ["budget", "location", "type", "bedrooms", "features"] as const;
const LABEL: Record<string, string> = { budget: "Budget", location: "Location", type: "Type", bedrooms: "Bedrooms", features: "Extras" };

/** Signature element: the score split into the five factors, each segment as wide as its weight,
 *  filled by the points it earned. Shows at a glance WHERE a property fits or falls short. */
export default function FitGauge({ score, breakdown, expanded = false }: { score: number; breakdown: Breakdown; expanded?: boolean }) {
  return (
    <div>
      <div className="flex items-center gap-3">
        <span className="w-12 text-right text-2xl font-semibold tabular-nums">{score}</span>
        <div className="flex h-3 flex-1 gap-0.5" role="img"
             aria-label={`Fit ${score} of 100. ` + ORDER.map((k) => `${LABEL[k]} ${breakdown[k]?.points}/${breakdown[k]?.max}`).join(", ")}>
          {ORDER.map((k) => {
            const b = breakdown[k];
            if (!b) return null;
            const ratio = b.points / b.max;
            return (
              <div key={k} style={{ flex: b.max }} className="overflow-hidden rounded-sm bg-pine-soft" title={`${LABEL[k]}: ${b.note}`}>
                <div className={ratio < 0.5 ? "h-full bg-brass" : "h-full bg-pine"} style={{ width: `${ratio * 100}%` }} />
              </div>
            );
          })}
        </div>
      </div>
      {expanded && (
        <dl className="mt-3 grid gap-x-6 gap-y-1 pl-[3.75rem] text-sm sm:grid-cols-2">
          {ORDER.map((k) => breakdown[k] && (
            <div key={k} className="flex justify-between gap-3">
              <dt className="text-muted">{LABEL[k]}</dt>
              <dd className={breakdown[k].points / breakdown[k].max < 0.5 ? "text-brass" : ""}>{breakdown[k].note}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

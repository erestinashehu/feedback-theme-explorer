import { Fragment, useEffect, useState } from "react";
import { api } from "../api.js";
import TrendChart from "../components/TrendChart.jsx";

const GRANULARITIES = [
  { key: "daily", label: "daily" },
  { key: "weekly", label: "weekly" },
  { key: "monthly", label: "monthly" },
];

export default function DashboardPage() {
  const [themes, setThemes] = useState(null);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [granularity, setGranularity] = useState("daily");
  const [trend, setTrend] = useState(null);
  const [trendLoading, setTrendLoading] = useState(false);

  const loadThemes = () => {
    api
      .listThemes()
      .then(setThemes)
      .catch((e) => setError(e.message));
  };

  useEffect(loadThemes, []);

  useEffect(() => {
    if (expandedId == null) return;
    setTrendLoading(true);
    api
      .themeTrend(expandedId, granularity)
      .then(setTrend)
      .finally(() => setTrendLoading(false));
  }, [expandedId, granularity]);

  if (error) {
    return (
      <p className="text-rust text-sm">
        Could not connect to the backend ({error}). Make sure the API is
        running on <span className="font-mono">localhost:8000</span>.
      </p>
    );
  }

  if (!themes) return <p className="text-sm text-muted">loading…</p>;

  if (themes.length === 0) {
    return (
      <div className="border hairline rounded p-8 text-center">
        <p className="font-serif text-xl mb-1">No themes yet</p>
        <p className="text-sm text-muted">
          Go to "Upload feedback" to add your first entries.
        </p>
      </div>
    );
  }

  const total = themes.reduce((s, t) => s + t.entry_count, 0);
  const sorted = [...themes].sort((a, b) => b.entry_count - a.entry_count);

  return (
    <div>
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="font-serif text-2xl">Discovered themes</h2>
        <p className="font-mono text-xs text-muted">
          {themes.length} themes · {total} entries total
        </p>
      </div>

      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b hairline text-left text-xs text-muted">
            <th className="py-2 font-normal">Theme</th>
            <th className="py-2 font-normal w-40">Share</th>
            <th className="py-2 font-normal w-16 text-right">Count</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((t) => {
            const pct = total ? Math.round((t.entry_count / total) * 100) : 0;
            const isOpen = expandedId === t.id;
            return (
              <Fragment key={t.id}>
                <tr
                  onClick={() => setExpandedId(isOpen ? null : t.id)}
                  className="border-b hairline cursor-pointer hover:bg-panel transition-colors"
                >
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      {t.is_recently_discovered && (
                        <span
                          title="Recently discovered theme"
                          className="w-1.5 h-1.5 rounded-full bg-ochre shrink-0"
                        />
                      )}
                      <span className="font-medium">{t.label}</span>
                    </div>
                    {t.summary && (
                      <p className="text-xs text-muted mt-0.5">{t.summary}</p>
                    )}
                  </td>
                  <td className="py-3 pr-4">
                    <div className="h-1.5 bg-line rounded overflow-hidden">
                      <div
                        className="h-full bg-ochre"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </td>
                  <td className="py-3 text-right font-mono">{t.entry_count}</td>
                </tr>
                {isOpen && (
                  <tr className="border-b hairline">
                    <td colSpan={3} className="pb-6 pt-2">
                      <div className="flex gap-2 mb-2">
                        {GRANULARITIES.map((g) => (
                          <button
                            key={g.key}
                            onClick={(e) => {
                              e.stopPropagation();
                              setGranularity(g.key);
                            }}
                            className={`text-xs px-2 py-1 rounded border hairline ${
                              granularity === g.key
                                ? "bg-ink text-paper border-ink"
                                : "text-muted hover:text-ink"
                            }`}
                          >
                            {g.label}
                          </button>
                        ))}
                      </div>
                      {trendLoading ? (
                        <p className="text-xs text-muted">loading…</p>
                      ) : (
                        trend && <TrendChart points={trend.points} granularity={granularity} />
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
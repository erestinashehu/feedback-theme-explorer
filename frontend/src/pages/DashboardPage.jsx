import { useEffect, useState } from "react";
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
        <p className="text-lg font-medium mb-1">No themes yet</p>
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
      <div className="flex items-baseline justify-between mb-5">
        <h2 className="text-lg font-medium">Discovered themes</h2>
        <p className="text-xs text-muted">
          {themes.length} themes · {total} entries total
        </p>
      </div>

      <div className="space-y-0.5">
        {sorted.map((t) => {
          const isOpen = expandedId === t.id;
          return (
            <div key={t.id}>
              <div
                onClick={() => setExpandedId(isOpen ? null : t.id)}
                className={`flex items-center gap-3 pl-4 pr-2 py-3.5 cursor-pointer hover:bg-panel hover:border-ochre transition-colors border-l-2 ${
                  isOpen ? "border-ochre" : "border-line"
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    {t.is_recently_discovered && (
                      <span
                        title="Recently discovered theme"
                        className="w-1.5 h-1.5 rounded-full bg-ochre shrink-0"
                      />
                    )}
                    <span className="text-sm font-medium">{t.label}</span>
                  </div>
                  {t.summary && (
                    <p className="text-xs text-muted mt-0.5">{t.summary}</p>
                  )}
                </div>
                <span className="font-mono text-sm text-muted">{t.entry_count}</span>
              </div>
              {isOpen && (
                <div className="pl-4 pb-5 pt-1 border-l-2 border-line">
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
                            ? "bg-ochre text-paper border-ochre"
                            : "text-muted hover:text-ochre hover:border-ochre"
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
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
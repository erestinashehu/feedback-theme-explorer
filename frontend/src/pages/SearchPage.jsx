import React, { useState } from "react";
import { api } from "../api.js";
import QuoteCard from "../components/QuoteCard.jsx";

const EXAMPLES = [
  "What are the top complaints this month?",
  "What are people saying about shipping?",
  "Are there any complaints about pricing?",
];

function AnsweredText({ text }) {
  const parts = text.split(/(\[\d+\])/g);
  return (
    <p className="leading-relaxed">
      {parts.map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (!m) return <span key={i}>{part}</span>;
        return React.createElement(
          "a",
          {
            key: i,
            href: "#entry-" + m[1],
            className: "font-mono text-xs align-super text-ochreDeep hover:underline",
          },
          part
        );
      })}
    </p>
  );
}

export default function SearchPage() {
  const [question, setQuestion] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const ask = async (q) => {
    const query = q ?? question;
    if (!query.trim()) return;
    setQuestion(query);
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.ask(
        query,
        dateFrom ? new Date(dateFrom).toISOString() : null,
        dateTo ? new Date(dateTo + "T23:59:59").toISOString() : null
      );
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h2 className="font-serif text-2xl mb-1">Ask your feedback</h2>
      <p className="text-sm text-muted mb-4">
        Answers are grounded only in the real feedback you've uploaded, with
        clear citations.
      </p>

      <div className="flex gap-3 mb-3">
        <label className="text-xs text-muted flex-1">
          from
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-full mt-1 border hairline rounded px-2 py-1.5 text-sm font-mono bg-panel"
          />
        </label>
        <label className="text-xs text-muted flex-1">
          to
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-full mt-1 border hairline rounded px-2 py-1.5 text-sm font-mono bg-panel"
          />
        </label>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="e.g. what are the top complaints this month?"
          className="flex-1 border hairline rounded px-3 py-2 text-sm bg-panel"
        />
        <button
          onClick={() => ask()}
          disabled={busy}
          className="px-4 py-2 text-sm bg-ink text-paper rounded hover:bg-ochreDeep transition-colors disabled:opacity-40"
        >
          {busy ? "…" : "Ask"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2 mt-3">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => ask(ex)}
            className="text-xs px-2 py-1 border hairline rounded text-muted hover:text-ink hover:border-ink"
          >
            {ex}
          </button>
        ))}
      </div>

      {error && <p className="text-rust text-sm mt-4">{error}</p>}

      {result && (
        <div className="mt-8">
          <div className="border hairline rounded p-4 bg-panel">
            <p className="font-mono text-[11px] text-muted mb-2">answer</p>
            <AnsweredText text={result.answer} />
          </div>

          {result.citations.length > 0 && (
            <div className="mt-6">
              <p className="font-mono text-[11px] text-muted mb-3">
                {result.citations.length} citations used
              </p>
              <div className="space-y-4">
                {result.citations.map((c) => (
                  <QuoteCard key={c.id} entry={c} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
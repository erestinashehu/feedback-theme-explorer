import { useState, useRef } from "react";
import { api } from "../api.js";

const PLACEHOLDER = `2026-08-02 | Order arrived 9 days late, nobody notified me
2026-08-03 | The material quality is great for the price
2026-08-04T14:20 | When will free return shipping be available?
2026-08-05 | The app crashed three times during checkout`;

function parseLines(raw) {
  const lines = raw
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const entries = [];
  const errors = [];

  lines.forEach((line, i) => {
    const sepIndex = line.indexOf("|");
    if (sepIndex === -1) {
      errors.push(`Line ${i + 1}: missing "|" separator between date and text`);
      return;
    }
    const rawDate = line.slice(0, sepIndex).trim();
    const content = line.slice(sepIndex + 1).trim();
    if (!content) {
      errors.push(`Line ${i + 1}: feedback text is empty`);
      return;
    }
    const iso = rawDate.length === 10 ? `${rawDate}T00:00:00` : rawDate;
    const date = new Date(iso);
    if (isNaN(date.getTime())) {
      errors.push(`Line ${i + 1}: date "${rawDate}" is not valid`);
      return;
    }
    entries.push({ content, feedback_at: date.toISOString() });
  });

  return { entries, errors };
}

export default function UploadPage() {
  const [raw, setRaw] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [parseErrors, setParseErrors] = useState([]);
  const fileRef = useRef(null);

  const handleFile = (file) => {
    const reader = new FileReader();
    reader.onload = () => setRaw((prev) => (prev ? prev + "\n" : "") + String(reader.result));
    reader.readAsText(file);
  };

  const handleSubmit = async () => {
    const { entries, errors } = parseLines(raw);
    setParseErrors(errors);
    if (entries.length === 0) return;

    setBusy(true);
    setResult(null);
    try {
      const res = await api.ingestBulk(entries);
      setResult(res);
    } catch (e) {
      setParseErrors([`Server error: ${e.message}`]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h2 className="text-lg font-medium mb-1">Upload feedback</h2>
      <p className="text-muted text-sm mb-5">
        One line per comment: date (and time, optional), then{" "}
        <span className="font-mono text-ink">|</span>, then the full text.
        You can paste directly or upload a{" "}
        <span className="font-mono">.txt</span> / <span className="font-mono">.csv</span> file
        in the same format.
      </p>

      <textarea
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        placeholder={PLACEHOLDER}
        rows={14}
        className="w-full bg-panel border hairline rounded p-4 font-mono placeholder:font-sans text-sm leading-relaxed resize-y focus:outline-none"
      />

      <div className="flex items-center gap-3 mt-3">
        <button
          onClick={() => fileRef.current?.click()}
          className="text-sm px-3 py-1.5 border hairline rounded hover:border-ochre transition-colors"
        >
          + upload file
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.csv"
          className="hidden"
          onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
        />
        <button
          onClick={handleSubmit}
          disabled={busy || !raw.trim()}
          className="ml-auto text-sm px-4 py-1.5 bg-ochre text-paper rounded hover:bg-ochreDeep transition-colors disabled:opacity-40"
        >
          {busy ? "processing…" : "Submit feedback"}
        </button>
      </div>

      {parseErrors.length > 0 && (
        <ul className="mt-4 text-sm text-rust space-y-1 border-l-2 border-rust pl-3">
          {parseErrors.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      )}

      {result && (
        <div className="mt-6 border hairline rounded p-4 bg-panel">
          <p className="font-mono text-xs text-muted mb-3">ingest result</p>
          <div className="grid grid-cols-3 gap-4 text-center mb-4">
            <Stat label="new entries" value={result.created} />
            <Stat label="matched existing theme" value={result.assigned_to_existing_theme} />
            <Stat label="sent to pool" value={result.sent_to_pool} />
          </div>
          {result.newly_discovered_themes.length > 0 && (
            <div>
              <p className="text-sm mb-2">
                <span className="text-ochreDeep font-medium">New themes discovered:</span>
              </p>
              <ul className="flex flex-wrap gap-2">
                {result.newly_discovered_themes.map((label, i) => (
                  <li
                    key={i}
                    className="text-sm px-2 py-1 border border-ochre text-ochreDeep rounded"
                  >
                    {label}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-2xl font-medium">{value}</p>
      <p className="text-xs text-muted mt-1">{label}</p>
    </div>
  );
}
export default function QuoteCard({ entry }) {
  const date = new Date(entry.feedback_at).toLocaleDateString("sq-AL", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });

  return (
    <div id={`entry-${entry.id}`} className="border-l-2 border-line pl-4 py-1">
      <p className="text-sm leading-relaxed">&ldquo;{entry.content}&rdquo;</p>
      <p className="mt-1 font-mono text-[11px] text-muted">
        [{entry.id}] · {date}
        {entry.theme_label && <> · {entry.theme_label}</>}
      </p>
    </div>
  );
}
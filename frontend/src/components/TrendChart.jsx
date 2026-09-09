import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

function formatTick(iso, granularity) {
  const d = new Date(iso);
  if (granularity === "monthly") {
    return d.toLocaleDateString("sq-AL", { month: "short", year: "2-digit" });
  }
  return d.toLocaleDateString("sq-AL", { day: "2-digit", month: "short" });
}

export default function TrendChart({ points, granularity }) {
  const data = points.map((p) => ({
    label: formatTick(p.period_start, granularity),
    count: p.count,
  }));

  if (data.length === 0) {
    return (
      <p className="text-sm text-muted py-8 text-center">
        S'ka ende te dhena te mjaftueshme per nje trend.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="#DBDFDA" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "#5B6B70", fontFamily: "IBM Plex Mono" }}
          axisLine={{ stroke: "#DBDFDA" }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: "#5B6B70", fontFamily: "IBM Plex Mono" }}
          axisLine={false}
          tickLine={false}
          width={28}
        />
        <Tooltip
          contentStyle={{
            fontSize: 12,
            fontFamily: "IBM Plex Mono",
            border: "1px solid #DBDFDA",
            borderRadius: 4,
          }}
        />
        <Bar dataKey="count" fill="#B8862B" radius={[2, 2, 0, 0]} maxBarSize={28} />
      </BarChart>
    </ResponsiveContainer>
  );
}
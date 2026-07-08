import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { label, value } = payload[0].payload;
  return (
    <div className="glass-panel px-3 py-2 text-xs shadow-card-hover">
      <p className="font-medium text-ink">{label}</p>
      <p className="data-figure mt-0.5 text-ink-muted">{value} / 100</p>
    </div>
  );
}

/**
 * Horizontal bar chart for comparing a handful of 0-100 subscores at a
 * glance -- used wherever a component used to just list "label: number"
 * rows. Each row can carry its own `tone` (a design-token color name)
 * and an optional `onClick`, so a chart can replace a clickable list
 * without losing the navigation.
 */
export function SubscoreBarChart({ data, height, barSize = 14 }) {
  const hasClicks = data.some((d) => d.onClick);
  return (
    <div>
      <ResponsiveContainer width="100%" height={height ?? data.length * 34 + 8}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            type="category"
            dataKey="label"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            stroke="var(--color-ink-muted)"
            width={100}
          />
          <Tooltip content={<BarTooltip />} cursor={{ fill: "var(--color-line)" }} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={barSize}>
            {data.map((d) => (
              <Cell
                key={d.label}
                fill={`var(--color-${d.tone})`}
                cursor={d.onClick ? "pointer" : "default"}
                onClick={d.onClick}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {hasClicks && <p className="mt-1 text-xs text-ink-faint">Click a bar for the full breakdown.</p>}
    </div>
  );
}

import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TONE_HEX } from "../../lib/chartColors";

function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { label, value } = payload[0].payload;
  return (
    <div className="glass-panel px-3 py-2 text-xs shadow-card-hover">
      <p className="font-medium text-ink">{label}</p>
      <p className="data-figure mt-0.5 text-ink-muted">{Math.round(value)} / 100</p>
    </div>
  );
}

/**
 * Vertical column chart for comparing a handful of 0-100 subscores at
 * a glance. Each column can carry its own `tone` (a design-token color
 * name) and an optional `onClick`, so a chart can replace a clickable
 * list without losing the navigation.
 */
export function SubscoreBarChart({ data, height = 220, barSize = 36 }) {
  const hasClicks = data.some((d) => d.onClick);
  // Angled labels only kick in once there are enough columns (and thus
  // narrow enough per-column width) that horizontal labels would
  // collide -- e.g. "Liquidity" and "Profitability" side by side.
  const angled = data.length > 3;

  return (
    <div>
      <ResponsiveContainer width="100%" height={angled ? height + 18 : height}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 8, bottom: angled ? 22 : 0, left: 0 }}
        >
          <CartesianGrid stroke="var(--color-line)" vertical={false} />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            fontSize={11}
            stroke="var(--color-ink-muted)"
            interval={0}
            angle={angled ? -35 : 0}
            textAnchor={angled ? "end" : "middle"}
            height={angled ? 40 : 30}
          />
          <YAxis type="number" domain={[0, 100]} hide />
          <Tooltip content={<BarTooltip />} cursor={{ fill: "var(--color-line)" }} />
          <Bar
            dataKey="value"
            radius={[5, 5, 0, 0]}
            barSize={barSize}
            activeBar={{ opacity: 0.8 }}
            isAnimationActive={false}
          >
            {data.map((d) => (
              <Cell
                key={d.label}
                fill={TONE_HEX[d.tone] ?? TONE_HEX["tier-4"]}
                cursor={d.onClick ? "pointer" : "default"}
                onClick={d.onClick}
              />
            ))}
            <LabelList
              dataKey="value"
              position="top"
              fill="#14181f"
              fontSize={12}
              fontWeight={600}
              formatter={(v) => Math.round(v)}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {hasClicks && <p className="mt-1 text-xs text-ink-faint">Click a bar for the full breakdown.</p>}
    </div>
  );
}

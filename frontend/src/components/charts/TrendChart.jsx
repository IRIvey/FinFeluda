import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCurrency } from "../../lib/utils";

function ChartTooltip({ active, payload, label, formatValue }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-panel px-3 py-2 text-xs shadow-card-hover">
      <p className="font-medium text-ink">{label}</p>
      <p className="data-figure mt-0.5 text-ink-muted">{formatValue(payload[0].value)}</p>
    </div>
  );
}

/** Shared trend chart used by Revenue/Profit/Debt/CashFlow/Expense charts — each is a thin config wrapper around this. */
export function TrendChart({ data, dataKey, label, color, formatValue = formatCurrency, emptyLabel }) {
  const hasData = Array.isArray(data) && data.some((row) => row[dataKey] !== null && row[dataKey] !== undefined);

  if (!hasData) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-line text-center">
        <p className="text-sm font-medium text-ink-muted">{label}</p>
        <p className="text-xs text-ink-faint">{emptyLabel ?? "No data available yet"}</p>
      </div>
    );
  }

  return (
    <div>
      <p className="mb-2 text-sm font-medium text-ink-muted">{label}</p>
      <ResponsiveContainer width="100%" height={192}>
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={`fill-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.25} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--color-line)" vertical={false} />
          <XAxis
            dataKey="year"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            stroke="var(--color-ink-faint)"
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            stroke="var(--color-ink-faint)"
            width={44}
            tickFormatter={(v) => formatValue(v)}
          />
          <Tooltip content={<ChartTooltip formatValue={formatValue} />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2}
            fill={`url(#fill-${dataKey})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

/** data: [{ metric: "Health score", A: number, B: number }, ...] */
export function ComparisonChart({ data, labelA, labelB }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--color-line)" vertical={false} />
        <XAxis dataKey="metric" tickLine={false} axisLine={false} fontSize={12} stroke="var(--color-ink-faint)" />
        <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="var(--color-ink-faint)" width={32} domain={[0, 100]} />
        <Tooltip />
        <Legend />
        <Bar dataKey="A" name={labelA} fill="var(--color-tier-1)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="B" name={labelB} fill="var(--color-tier-2)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

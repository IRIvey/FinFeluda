import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { RevenueChart } from "../charts/RevenueChart";
import { ProfitChart } from "../charts/ProfitChart";
import { ExpenseChart } from "../charts/ExpenseChart";
import { DebtChart } from "../charts/DebtChart";
import { CashFlowChart } from "../charts/CashFlowChart";
import { formatCurrency } from "../../lib/utils";

export function FinancialDashboard({ financials }) {
  const hasData = Array.isArray(financials) && financials.length > 0;
  const sorted = hasData ? [...financials].sort((a, b) => a.year - b.year) : [];

  return (
    <Card title="Financial dashboard">
      {!hasData ? (
        <EmptyState>
          No yearly financials have been extracted for this investigation yet.
        </EmptyState>
      ) : (
        <div className="flex flex-col gap-8">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <RevenueChart data={sorted} />
            <ProfitChart data={sorted} />
            <ExpenseChart data={sorted} />
            <DebtChart data={sorted} />
            <CashFlowChart data={sorted} />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line text-xs uppercase tracking-wide text-ink-faint">
                  <th className="py-2 pr-4 font-medium">Year</th>
                  <th className="py-2 pr-4 font-medium">Revenue</th>
                  <th className="py-2 pr-4 font-medium">Profit</th>
                  <th className="py-2 pr-4 font-medium">Expenses</th>
                  <th className="py-2 pr-4 font-medium">Debt</th>
                  <th className="py-2 font-medium">Cash flow</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((row) => (
                  <tr key={row.year} className="border-b border-line last:border-0">
                    <td className="data-figure py-2 pr-4 text-ink">{row.year}</td>
                    <td className="data-figure py-2 pr-4 text-ink-muted">
                      {formatCurrency(row.revenue, row.currency)}
                    </td>
                    <td className="data-figure py-2 pr-4 text-ink-muted">
                      {formatCurrency(row.profit, row.currency)}
                    </td>
                    <td className="data-figure py-2 pr-4 text-ink-muted">
                      {formatCurrency(row.expenses, row.currency)}
                    </td>
                    <td className="data-figure py-2 pr-4 text-ink-muted">
                      {formatCurrency(row.debt, row.currency)}
                    </td>
                    <td className="data-figure py-2 text-ink-muted">
                      {formatCurrency(row.cash_flow, row.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Card>
  );
}

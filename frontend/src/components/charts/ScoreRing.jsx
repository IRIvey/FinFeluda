import { motion } from "framer-motion";
import { TONE_HEX } from "../../lib/chartColors";

/** Single-ring circular progress gauge for a 0-100 score -- compact
    replacement for a bare "NN / 100" headline number. */
export function ScoreRing({ value, tone, label, size = 92, strokeWidth = 9 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, value ?? 0));
  const color = TONE_HEX[tone] ?? TONE_HEX["tier-4"];

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-line)"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - pct / 100) }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="data-figure text-2xl font-semibold" style={{ color }}>
          {value ?? "—"}
        </span>
        {label && <span className="text-[10px] font-medium text-ink-faint">{label}</span>}
      </div>
    </div>
  );
}

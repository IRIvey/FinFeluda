import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  motion,
  MotionConfig,
  animate,
  useMotionValue,
  useSpring,
  useTransform,
  useMotionTemplate,
  useReducedMotion,
} from "framer-motion";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { BrandMark } from "../components/layout/BrandMark";
import { cn, CONFIDENCE_TIER_META } from "../lib/utils";
import glassImg from "../assets/glass.png";

const FEATURES = [
  {
    tag: "FH",
    title: "Financial health score",
    copy: "Growth, liquidity, profitability, debt, and efficiency — five subscores rolled into one number you can defend.",
  },
  {
    tag: "RA",
    title: "Risk analysis",
    copy: "Financial, operational, and business risk, each backed by concrete red flags and a severity rating.",
  },
  {
    tag: "CD",
    title: "Contradiction detection",
    copy: "Cross-references what a company claims against independent public signal, and flags where they disagree.",
  },
  {
    tag: "ST",
    title: "Full source trail",
    copy: "Every source the AI actually fetched, grouped by how much to trust it, with a link back to the original.",
  },
  {
    tag: "CO",
    title: "Side-by-side compare",
    copy: "Put two investigations next to each other and get an AI-written comparison, not just a table of numbers.",
  },
  {
    tag: "PD",
    title: "Downloadable report",
    copy: "One PDF with the summary, the numbers, and the reasoning behind them — ready to forward.",
  },
];

const STEPS = [
  {
    title: "Point it at a company",
    copy: "Upload a filing or pitch deck, drop in a website URL, or both. No login, no setup.",
  },
  {
    title: "Let it investigate",
    copy: "It gathers public evidence, scores what it finds, and tags every claim with how much to trust it.",
  },
  {
    title: "Read a report that shows its work",
    copy: "Health score, red flags, executive summary, and a source for every figure — export it when you're done.",
  },
];

const revealUp = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

const staggerGroup = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

function LandingNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper/85 backdrop-blur-sm">
      <div className="mx-auto flex min-h-16 w-full max-w-6xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-6 py-2 md:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <BrandMark tagline />
        </Link>

        <div className="flex items-center gap-1">
          <Link
            to="/dashboard"
            className="rounded-lg px-2.5 py-2 text-sm font-medium text-ink-muted transition-colors hover:bg-black/[0.03] hover:text-ink sm:px-3"
          >
            Dashboard
          </Link>
          <Link
            to="/compare"
            className="rounded-lg px-2.5 py-2 text-sm font-medium text-ink-muted transition-colors hover:bg-black/[0.03] hover:text-ink sm:px-3"
          >
            Compare
          </Link>
          <Button as={Link} to="/new" variant="primary" size="sm" className="ml-2">
            Get started
          </Button>
        </div>
      </div>
    </header>
  );
}

function FloatingChip({ label, value, tone, className, float = 8, duration = 5, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: [0, -float, 0] }}
      transition={{
        opacity: { duration: 0.4, delay: delay + 1.4 },
        y: { duration, delay: delay + 1.4, repeat: Infinity, ease: "easeInOut" },
      }}
      className={cn("glass-card absolute z-10 px-4 py-2.5", className)}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-faint">{label}</p>
      <p className="data-figure text-xl font-semibold" style={{ color: `var(--color-${tone})` }}>
        {value}
      </p>
    </motion.div>
  );
}

function MagnifierHero() {
  return (
    <div className="relative w-full max-w-md shrink-0">
      {/* Soft brand glow behind the report, breathing slowly. */}
      <motion.div
        aria-hidden="true"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.5, 0.85, 0.5], scale: [1, 1.06, 1] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -inset-8 rounded-full bg-brand-soft blur-3xl"
      />

      <FloatingChip
        label="Health score"
        value="62"
        tone="tier-3"
        className="-top-6 -right-3 sm:-right-8"
        duration={5}
      />
      <FloatingChip
        label="Risk score"
        value="58"
        tone="risk-high"
        className="-top-12 -left-3 sm:-left-8"
        duration={5.5}
        delay={1}
        float={7}
      />
      <FloatingChip
        label="Red flags"
        value="3"
        tone="risk-high"
        className="-bottom-6 -left-3 sm:-left-8"
        duration={6}
        delay={0.6}
        float={6}
      />
      <FloatingChip
        label="Sources"
        value="14"
        tone="tier-1"
        className="-bottom-12 -right-3 sm:-right-8"
        duration={6.5}
        delay={1.4}
        float={5}
      />

      <LensViewer />

      <p className="mt-4 text-center text-xs text-ink-faint">
        Move the lens to read the annotated report beneath the summary.
      </p>
    </div>
  );
}

/**
 * Shared chrome around whichever report content sits inside it.
 *
 * `fill` is used for the ghost summary: it stretches to match the grid
 * row (which the taller report defines) so both layers render as the
 * same size "sheet of paper" even though their content lengths differ.
 * The report itself must NOT stretch -- its natural, un-forced height
 * is what the grid-stacked layout in LensViewer measures to size the
 * row at all.
 */
function ReportShell({ eyebrow, children, fill = false }) {
  return (
    <div className={cn("glass-panel flex flex-col overflow-hidden", fill && "h-full")}>
      <div className="flex items-center justify-between border-b border-line px-5 py-3">
        <div className="flex items-center gap-2">
          <span aria-hidden="true" className="h-2 w-2 rounded-full bg-brand" />
          <p className="font-display text-sm font-semibold text-ink">Fenwick Grid Systems</p>
        </div>
        <span className="tier-tag bg-line text-ink-faint">{eyebrow}</span>
      </div>
      <div className="flex-1 px-5 py-4">{children}</div>
    </div>
  );
}

/** What a skim-read gives you: confident, vague, and unsourced. It's a
    full page of text like the real report -- just none of it grounded
    in anything, which is the point the lens makes when it lands here. */
function SummaryGhost() {
  return (
    <ReportShell eyebrow="Quick summary" fill>
      <p className="text-sm leading-relaxed text-ink-muted">
        Fenwick Grid Systems is a clean-energy company posting steady growth, with an
        expanding storage product line and a positive investor narrative heading into
        FY2025.
      </p>
      <p className="mt-3 text-sm leading-relaxed text-ink-muted">
        The business has scaled its go-to-market team and continues to sign new utility
        partnerships, with leadership pointing to a strong pipeline for the year ahead.
      </p>
      <p className="mt-3 text-sm leading-relaxed text-ink-muted">
        Overall trajectory looks positive, and management sounds confident about
        FY2025 in every public appearance so far.
      </p>
      <p className="mt-3 text-sm leading-relaxed text-ink-faint italic">
        No specific concerns are flagged in this overview.
      </p>
    </ReportShell>
  );
}

/** Inline citation-style highlight — the evidence-tier motif, embedded in prose. */
function Evidence({ tier, children }) {
  const meta = CONFIDENCE_TIER_META[tier];
  return (
    <span
      className="rounded-[3px] px-0.5"
      style={{
        backgroundColor: `var(--color-${meta.color}-soft)`,
        boxShadow: `inset 0 -2px 0 var(--color-${meta.color})`,
      }}
    >
      {children}
      <sup className="ml-0.5 font-mono text-[9px] font-semibold" style={{ color: `var(--color-${meta.color})` }}>
        {tier}
      </sup>
    </span>
  );
}

const KEY_FIGURES = [
  { label: "Revenue", value: "$55.3M" },
  { label: "Debt", value: "$24M" },
  { label: "Cash flow", value: "$2.4M" },
];

const SCORE_BARS = [
  { label: "Health", value: 62, tone: "tier-3" },
  { label: "Risk", value: 58, tone: "risk-high" },
];

/** Same score-bar idea now used across the real app's report panels --
    animates in once, the moment the hero is on screen. */
function MiniScoreBars() {
  return (
    <div className="flex flex-col gap-2">
      {SCORE_BARS.map((row) => (
        <div key={row.label} className="flex items-center gap-3">
          <span className="w-11 shrink-0 text-[10px] font-semibold uppercase tracking-wide text-ink-faint">
            {row.label}
          </span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-line">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: `var(--color-${row.tone})` }}
              initial={{ width: 0 }}
              whileInView={{ width: `${row.value}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
            />
          </div>
          <span
            className="data-figure w-6 shrink-0 text-right text-sm font-semibold"
            style={{ color: `var(--color-${row.tone})` }}
          >
            {row.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/** What the lens actually reveals: sourced, tiered, specific -- and long
    enough that panning the lens genuinely uncovers new material. */
function ReportDetail() {
  return (
    <ReportShell eyebrow="Full report">
      <MiniScoreBars />

      <p className="mt-3 text-sm leading-relaxed text-ink">
        Revenue grew <Evidence tier={1}>34% YoY in FY2024</Evidence>, partly funded by{" "}
        <Evidence tier={1}>$18M in acquisition debt taken on in 2023</Evidence>. Operating
        margin compressed to <Evidence tier={1}>6% as service costs outpaced hardware sales</Evidence>,
        leaving roughly <Evidence tier={1}>five months of runway</Evidence> at the current burn rate.
      </p>

      <p className="mt-3 text-sm leading-relaxed text-ink">
        Independent coverage flags <Evidence tier={3}>rising employee turnover since 2023</Evidence>{" "}
        and <Evidence tier={3}>customer concentration — the top three utility contracts are 41%
        of revenue</Evidence>. The founder's claim of being{" "}
        <Evidence tier={4}>"the category leader"</Evidence> contradicts independent
        market-share data.
      </p>

      <div className="mt-4 grid grid-cols-3 gap-3 border-t border-line pt-3 text-center">
        {KEY_FIGURES.map((f) => (
          <div key={f.label}>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-faint">{f.label}</p>
            <p className="data-figure text-sm font-semibold text-ink">{f.value}</p>
          </div>
        ))}
      </div>

      <p className="mt-3 flex items-center gap-1.5 text-xs font-medium text-risk-high">
        <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-risk-high" />
        3 red flags identified — 1 is a contradiction
      </p>
      <p className="mt-2 text-xs text-ink-faint">
        Sourced from the SEC 10-K, the company site, 6 independent articles, and
        employee reviews — 14 sources checked in total.
      </p>
    </ReportShell>
  );
}

const LENS_RADIUS = 68;
const MAGNIFICATION = 1.4;

/* glass.png is a 512x512 outline icon; the see-through hole isn't
   centered on the canvas (there's a handle reaching toward the
   bottom-right corner). Measured directly from the file's alpha channel
   (flood-fill from the border to isolate the enclosed transparent hole):
   center (215.0, 211.5), radius 179.8px. Scaling the image so that
   radius equals LENS_RADIUS keeps the visible hole exactly aligned with
   the clip-path circle below. */
const LENS_HOLE_CENTER_FRAC_X = 215.0 / 512;
const LENS_HOLE_CENTER_FRAC_Y = 211.5 / 512;
const LENS_HOLE_RADIUS_FRAC = 179.8 / 512;
const LENS_IMG_SIZE = LENS_RADIUS / LENS_HOLE_RADIUS_FRAC;
const LENS_IMG_OFFSET_X = LENS_HOLE_CENTER_FRAC_X * LENS_IMG_SIZE;
const LENS_IMG_OFFSET_Y = LENS_HOLE_CENTER_FRAC_Y * LENS_IMG_SIZE;

/**
 * Magnifying-glass hero: a vague AI summary sits ghosted underneath;
 * the lens reveals the real, source-tiered report at true magnification
 * wherever it passes. Follows the cursor; when idle (or on touch
 * devices) it sweeps the document on its own.
 */
function LensViewer() {
  const containerRef = useRef(null);
  const [hovering, setHovering] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  const mx = useMotionValue(180);
  const my = useMotionValue(160);
  const sx = useSpring(mx, { stiffness: 200, damping: 24 });
  const sy = useSpring(my, { stiffness: 200, damping: 24 });

  const clipPath = useMotionTemplate`circle(${LENS_RADIUS}px at ${sx}px ${sy}px)`;
  const transformOrigin = useMotionTemplate`${sx}px ${sy}px`;
  const lensImgX = useTransform(sx, (v) => v - LENS_IMG_OFFSET_X);
  const lensImgY = useTransform(sy, (v) => v - LENS_IMG_OFFSET_Y);

  useEffect(() => {
    if (hovering || prefersReducedMotion) return;
    const ax = animate(mx, [90, 340, 200, 90], {
      duration: 12,
      repeat: Infinity,
      ease: "easeInOut",
    });
    const ay = animate(my, [110, 160, 380, 110], {
      duration: 12,
      repeat: Infinity,
      ease: "easeInOut",
    });
    return () => {
      ax.stop();
      ay.stop();
    };
  }, [hovering, prefersReducedMotion, mx, my]);

  const handleMove = (e) => {
    const rect = containerRef.current.getBoundingClientRect();
    mx.set(e.clientX - rect.left);
    my.set(e.clientY - rect.top);
  };

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4, ease: "easeOut" }}
      onPointerMove={handleMove}
      onPointerEnter={() => setHovering(true)}
      onPointerLeave={() => setHovering(false)}
      className="relative grid cursor-none"
    >
      {/* Ghosted summary — what a skim-read gives you. Both layers share
          grid-area 1/1 so the container auto-sizes to the taller one. */}
      <div
        className="[grid-area:1/1]"
        style={{ filter: "grayscale(1) blur(2px)", opacity: 0.45 }}
        aria-hidden="true"
      >
        <SummaryGhost />
      </div>

      {/* The real report, magnified, visible only through the lens. Stays
          a normal (non-absolute) grid item so its natural height -- taller
          than the ghost's -- is what the auto-sizing row picks up. */}
      <motion.div className="[grid-area:1/1] overflow-hidden" style={{ clipPath }}>
        <motion.div style={{ scale: MAGNIFICATION, transformOrigin }}>
          <ReportDetail />
        </motion.div>
      </motion.div>

      {/* The lens itself. */}
      <motion.img
        src={glassImg}
        alt=""
        aria-hidden="true"
        draggable={false}
        className="pointer-events-none absolute left-0 top-0 [grid-area:1/1] z-20 select-none"
        style={{
          x: lensImgX,
          y: lensImgY,
          width: LENS_IMG_SIZE,
          height: LENS_IMG_SIZE,
          filter:
            "drop-shadow(0 16px 20px rgba(20,24,31,0.4)) drop-shadow(0 4px 8px rgba(20,24,31,0.25))",
        }}
      />
    </motion.div>
  );
}

function FeatureGrid() {
  return (
    <motion.div
      variants={staggerGroup}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
    >
      {FEATURES.map((f) => (
        <motion.div
          key={f.title}
          variants={revealUp}
          whileHover={{ y: -3 }}
          className="glass-card p-6 transition-shadow hover:shadow-card-hover"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-soft font-mono text-[11px] font-semibold text-brand-deep">
            {f.tag}
          </span>
          <h3 className="mt-4 font-display text-lg font-semibold text-ink">{f.title}</h3>
          <p className="mt-2 text-sm text-ink-muted">{f.copy}</p>
        </motion.div>
      ))}
    </motion.div>
  );
}

function TierLegend() {
  return (
    <motion.div
      variants={staggerGroup}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.4 }}
      className="glass-panel grid grid-cols-1 divide-y divide-line sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-4"
    >
      {Object.entries(CONFIDENCE_TIER_META).map(([tierNum, meta]) => (
        <motion.div key={tierNum} variants={revealUp} className="p-5">
          <Badge color={meta.color}>Tier {tierNum} · {meta.label}</Badge>
          <p className="mt-3 text-sm text-ink-muted">
            {
              {
                1: "Primary filings and official records — SEC, company financials.",
                2: "Company-controlled but published channels — its own site, its own repos.",
                3: "Independent coverage that lines up with the claim — news, reviews.",
                4: "Unconfirmed or contradicted by independent signal — flagged, not hidden.",
              }[tierNum]
            }
          </p>
        </motion.div>
      ))}
    </motion.div>
  );
}

function HowItWorks() {
  return (
    <motion.div
      variants={staggerGroup}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.3 }}
      className="grid grid-cols-1 gap-8 md:grid-cols-3"
    >
      {STEPS.map((step, i) => (
        <motion.div key={step.title} variants={revealUp}>
          <span className="data-figure flex h-8 w-8 items-center justify-center rounded-md bg-brand-soft text-sm font-semibold text-brand-deep">
            {i + 1}
          </span>
          <h3 className="mt-4 font-display text-lg font-semibold text-ink">{step.title}</h3>
          <p className="mt-2 text-sm text-ink-muted">{step.copy}</p>
        </motion.div>
      ))}
    </motion.div>
  );
}

export function LandingPage() {
  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-screen bg-paper">
        <LandingNav />

        <section className="mx-auto w-full max-w-6xl px-6 pt-16 pb-20 md:px-8 md:pt-24">
          <div className="flex flex-col items-start gap-14 lg:flex-row lg:items-start lg:justify-between">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="max-w-xl"
            >
              <h1 className="font-display text-4xl font-semibold text-ink sm:text-5xl">
                Diligence that shows its work.
              </h1>
              <p className="mt-5 text-base text-ink-muted">
                Point FinFeluda at a company's filings, pitch deck, or website. It gathers
                evidence from public sources, scores what it finds, and tags every claim with
                how much you should trust it — so you're never just taking the AI's word for it.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Button as={Link} to="/new" variant="primary" size="lg">
                  Get started
                </Button>
                <Button as={Link} to="/dashboard" variant="secondary" size="lg">
                  View the dashboard
                </Button>
              </div>
            </motion.div>

            <MagnifierHero />
          </div>
        </section>

        <section className="border-t border-line">
          <div className="mx-auto w-full max-w-6xl px-6 py-20 md:px-8">
            <motion.div
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.6 }}
              variants={revealUp}
              className="mb-10 max-w-xl"
            >
              <p className="font-mono text-xs font-semibold tracking-[0.14em] text-brand uppercase">
                What it does
              </p>
              <h2 className="mt-2 font-display text-3xl font-semibold text-ink">
                One upload, a full investigation.
              </h2>
            </motion.div>
            <FeatureGrid />
          </div>
        </section>

        <section className="border-t border-line bg-surface">
          <div className="mx-auto w-full max-w-6xl px-6 py-20 md:px-8">
            <motion.div
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.6 }}
              variants={revealUp}
              className="mb-10 max-w-xl"
            >
              <p className="font-mono text-xs font-semibold tracking-[0.14em] text-brand uppercase">
                The evidence ledger
              </p>
              <h2 className="mt-2 font-display text-3xl font-semibold text-ink">
                Four tiers. No claim graded on vibes.
              </h2>
              <p className="mt-3 text-sm text-ink-muted">
                Every figure and red flag in a FinFeluda report carries one of these — drawn
                straight from where the AI actually found it.
              </p>
            </motion.div>
            <TierLegend />
          </div>
        </section>

        <section className="mx-auto w-full max-w-6xl px-6 py-20 md:px-8">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.6 }}
            variants={revealUp}
            className="mb-10 max-w-xl"
          >
            <p className="font-mono text-xs font-semibold tracking-[0.14em] text-brand uppercase">
              How it works
            </p>
            <h2 className="mt-2 font-display text-3xl font-semibold text-ink">
              Three steps, a few minutes.
            </h2>
          </motion.div>
          <HowItWorks />
        </section>

        <section className="border-t border-line bg-brand-soft">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.6 }}
            variants={revealUp}
            className="mx-auto flex w-full max-w-6xl flex-col items-start justify-between gap-6 px-6 py-16 md:flex-row md:items-center md:px-8"
          >
            <div>
              <h2 className="font-display text-2xl font-semibold text-ink sm:text-3xl">
                Start your first investigation.
              </h2>
              <p className="mt-2 max-w-md text-sm text-ink-muted">
                Upload a document or point at a website — the first report takes a few minutes.
              </p>
            </div>
            <Button as={Link} to="/new" variant="primary" size="lg">
              Get started
            </Button>
          </motion.div>
        </section>

        <footer className="border-t border-line">
          <div className="mx-auto flex w-full max-w-6xl flex-col items-start justify-between gap-4 px-6 py-10 text-sm text-ink-faint md:flex-row md:items-center md:px-8">
            <div className="flex items-center gap-2.5">
              <BrandMark iconSize="h-6 w-6" textSize="text-sm" />
            </div>
            <div className="flex items-center gap-5">
              <Link to="/dashboard" className="hover:text-ink">Dashboard</Link>
              <Link to="/compare" className="hover:text-ink">Compare</Link>
              <Link to="/new" className="hover:text-ink">New investigation</Link>
            </div>
          </div>
        </footer>
      </div>
    </MotionConfig>
  );
}

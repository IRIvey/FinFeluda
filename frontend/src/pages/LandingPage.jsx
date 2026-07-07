import { Link } from "react-router-dom";
import { motion, MotionConfig } from "framer-motion";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { cn, CONFIDENCE_TIER_META } from "../lib/utils";

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

const MOCK_CLAIMS = [
  { text: "Revenue grew 34% YoY in FY2024", tier: 1, source: "SEC 10-K filing", icon: "filing" },
  { text: "Took on $18M in debt to fund a 2023 acquisition", tier: 1, source: "SEC 10-K filing", icon: "filing" },
  { text: "Employee reviews cite rising turnover since 2023", tier: 3, source: "Corroborating press", icon: "press" },
  { text: "Founder calls it “the category leader”", tier: 4, source: "Contradicts market-share data", icon: "quote" },
];

/* Small evidence-source glyphs so each ledger row reads at a glance:
   a filing document, independent press, or a company's own words. */
const SOURCE_ICONS = {
  filing: (
    <svg className="h-full w-full" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 1.5h5.5L12.5 4.5v10h-8.5z" />
      <path d="M9.5 1.5v3h3" />
      <path d="M6 8h4.5M6 10.5h4.5" />
    </svg>
  ),
  press: (
    <svg className="h-full w-full" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3.5h9.5v9a1 1 0 0 0 1 1H3a1 1 0 0 1-1-1z" />
      <path d="M11.5 6H14v6.5a1 1 0 0 1-1 1h-.5" />
      <path d="M4.5 6.5h4.5M4.5 9h4.5M4.5 11h2.5" />
    </svg>
  ),
  quote: (
    <svg className="h-full w-full" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2.5 3h11v8h-6L4 13.5V11H2.5z" />
      <path d="M5.5 6.5h5M5.5 8.5h3" />
    </svg>
  ),
};

const heroContainer = {
  hidden: {},
  show: { transition: { staggerChildren: 0.16, delayChildren: 0.5 } },
};

const heroRow = {
  hidden: { opacity: 0, x: -10 },
  show: { opacity: 1, x: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

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
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-brand text-xs font-semibold text-white">
            FF
          </span>
          <span className="flex flex-col leading-none">
            <span className="font-display text-base font-semibold text-ink">FinFeluda</span>
            <span className="hidden text-[11px] tracking-wide text-ink-faint sm:block">
              AI Due Diligence Copilot
            </span>
          </span>
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

function EvidenceLedgerDemo() {
  return (
    <div className="relative w-full max-w-md shrink-0">
      {/* Soft brand glow behind the ledger, breathing slowly. */}
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
        label="Red flags"
        value="3"
        tone="risk-high"
        className="-bottom-6 -left-3 sm:-left-8"
        duration={6}
        delay={0.6}
        float={6}
      />

      <motion.div
        variants={heroContainer}
        initial="hidden"
        animate="show"
        className="glass-panel relative overflow-hidden"
      >
        {/* Periodic scan sweep — the "AI reading the ledger" moment. */}
        <motion.div
          aria-hidden="true"
          initial={{ top: "-12%", opacity: 0 }}
          animate={{ top: ["-12%", "108%"], opacity: [0, 0.7, 0.7, 0] }}
          transition={{ duration: 2.4, delay: 2.2, repeat: Infinity, repeatDelay: 3.6, ease: "easeInOut" }}
          className="pointer-events-none absolute left-0 z-10 h-10 w-full"
          style={{
            background:
              "linear-gradient(to bottom, transparent, color-mix(in srgb, var(--color-brand) 12%, transparent), transparent)",
          }}
        />

        <div className="flex items-center justify-between border-b border-line px-5 py-3">
          <div className="flex items-center gap-2">
            <motion.span
              aria-hidden="true"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
              className="h-2 w-2 rounded-full bg-brand"
            />
            <p className="font-display text-sm font-semibold text-ink">Fenwick Grid Systems</p>
          </div>
          <span className="tier-tag bg-line text-ink-faint">Sample investigation</span>
        </div>
        <ul className="flex flex-col divide-y divide-line">
          {MOCK_CLAIMS.map((claim) => {
            const tier = CONFIDENCE_TIER_META[claim.tier];
            return (
              <motion.li
                key={claim.text}
                variants={heroRow}
                whileHover={{ backgroundColor: "rgba(20, 24, 31, 0.02)" }}
                className="relative flex items-start gap-3 py-3 pr-4 pl-[calc(1.25rem-3px)]"
              >
                <span
                  aria-hidden="true"
                  className="absolute left-0 top-0 h-full w-[3px]"
                  style={{ backgroundColor: `var(--color-${tier.color})` }}
                />
                <span
                  aria-hidden="true"
                  className="mt-0.5 h-6 w-6 shrink-0 rounded-md p-1"
                  style={{
                    backgroundColor: `var(--color-${tier.color}-soft)`,
                    color: `var(--color-${tier.color})`,
                  }}
                >
                  {SOURCE_ICONS[claim.icon]}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-ink">{claim.text}</p>
                  <p className="mt-1 text-[11px] text-ink-faint">{claim.source}</p>
                </div>
                <Badge color={tier.color} className="mt-0.5 shrink-0">
                  {tier.label}
                </Badge>
              </motion.li>
            );
          })}
        </ul>
      </motion.div>
    </div>
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
          <div className="flex flex-col items-start gap-14 lg:flex-row lg:items-center lg:justify-between">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="max-w-xl"
            >
              <p className="font-mono text-xs font-semibold tracking-[0.14em] text-brand uppercase">
                AI due diligence, no login required
              </p>
              <h1 className="mt-4 font-display text-4xl font-semibold text-ink sm:text-5xl">
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

            <EvidenceLedgerDemo />
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
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-brand text-[10px] font-semibold text-white">
                FF
              </span>
              <span className="font-display text-sm font-semibold text-ink">FinFeluda</span>
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

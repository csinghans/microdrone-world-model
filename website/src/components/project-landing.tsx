import Image from "next/image";

import evidenceJson from "@/content/evidence.json";
import {
  siteCopy,
  type EvidenceKey,
  type Locale,
} from "@/content/site-copy";
import { FlightClip } from "@/components/flight-clip";
import { GITHUB_URL, sitePath } from "@/lib/site";

type EvidenceData = {
  gateOfRecord: string;
  transit: {
    successes: number;
    missions: number;
    successRate: number;
    source: string;
  };
  indoor: {
    successes: number;
    missions: number;
    successRate: number;
    collisionMissions: number;
    source: string;
  };
  embedded: {
    version: string;
    totalKb: number;
    budgetKb: number;
    macsMillions: number;
    assumedThroughputGmacs: number;
    estimatedLatencyMs: number;
    source: string;
  };
};

const evidence = evidenceJson as EvidenceData;

const rerunCommands: Record<EvidenceKey, string> = {
  transit: "python -m scripts.gate --run-transit 100",
  indoor: "python -m scripts.gate --run-indoor 100",
  embedded: "python -m eval.eval_latency_budget --selftest",
  latency: "python -m eval.eval_latency_budget --selftest",
};

function evidenceSource(key: EvidenceKey): string {
  if (key === "transit") return evidence.transit.source;
  if (key === "indoor") return evidence.indoor.source;
  return evidence.embedded.source;
}

function evidenceValue(key: EvidenceKey): string {
  if (key === "transit") {
    return `${evidence.transit.successes}/${evidence.transit.missions}`;
  }
  if (key === "indoor") {
    return `${evidence.indoor.successes}/${evidence.indoor.missions}`;
  }
  if (key === "embedded") return `${evidence.embedded.totalKb} KB`;
  return `≈ ${evidence.embedded.estimatedLatencyMs} ms`;
}

function evidenceStatus(key: EvidenceKey, locale: Locale): string {
  if (key === "transit" || key === "indoor") {
    return locale === "zh-TW" ? "通過" : "pass";
  }
  if (key === "embedded") {
    return `< ${evidence.embedded.budgetKb} KB`;
  }
  return locale === "zh-TW" ? "推算" : "estimated";
}

type ProjectLandingProps = {
  locale: Locale;
};

export function ProjectLanding({ locale }: ProjectLandingProps) {
  const copy = siteCopy[locale];
  const isZh = locale === "zh-TW";
  const homeHref = sitePath(isZh ? "/zh/" : "/");
  const languageHref = sitePath(isZh ? "/" : "/zh/");
  const guideUrl = `${GITHUB_URL}/blob/main/docs/START-HERE.zh-TW.md`;
  const ideasUrl = `${GITHUB_URL}/blob/main/docs/RESEARCH-IDEAS.md`;

  return (
    <div className="site-shell">
      <a className="skip-link" href="#main-content">
        {copy.accessibility.skip}
      </a>

      <header className="topbar">
        <div className="topbar__inner">
          <a className="brand" href={homeHref} aria-label={copy.brand.homeLabel}>
            <span className="brand__mark" aria-hidden="true">
              μ
            </span>
            <span className="brand__text">
              <span>{copy.brand.name}</span>
              <small>{copy.brand.descriptor}</small>
            </span>
          </a>

          <nav className="topbar__nav" aria-label={isZh ? "主要導覽" : "Primary navigation"}>
            <span className="nav__primary">
              {copy.nav.map((item) => (
                <a key={item.href} href={item.href}>
                  {item.label}
                </a>
              ))}
            </span>
            <a className="nav__github" href={GITHUB_URL}>
              {copy.brand.githubLabel}
            </a>
            <a
              className="nav__language"
              href={languageHref}
              hrefLang={isZh ? "en" : "zh-Hant"}
              lang={isZh ? "en" : "zh-Hant"}
            >
              {copy.brand.languageLabel}
            </a>
          </nav>
        </div>
      </header>

      <main id="main-content" className="page-main">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero__copy">
            <p className="eyebrow">{copy.hero.eyebrow}</p>
            <h1 id="hero-title">{copy.hero.title}</h1>
            <p className="hero__lede">{copy.hero.lede}</p>
            <div className="hero__actions">
              <a className="button-link button-link--primary" href="#evidence">
                {copy.hero.primaryCta}
                <span aria-hidden="true">↓</span>
              </a>
              <a className="button-link" href={GITHUB_URL}>
                {copy.hero.secondaryCta}
                <span aria-hidden="true">↗</span>
              </a>
            </div>
          </div>

          <div className="hero__record">
            <div className="record__topline">
              <span>{copy.hero.recordLabel}</span>
              <span>{copy.hero.recordStatus}</span>
            </div>
            <FlightClip
              src={sitePath("/media/hero-course.mp4")}
              poster={sitePath("/media/hero-course.webp")}
              title={copy.hero.media.title}
              description={copy.hero.media.description}
              ariaLabel={copy.hero.media.ariaLabel}
              playLabel={copy.accessibility.play}
              pauseLabel={copy.accessibility.pause}
              priority
            />
            <div className="record__metrics" aria-label={isZh ? "正式模擬紀錄摘要" : "Formal simulation record summary"}>
              <div className="record__metric">
                <strong>
                  {evidence.transit.successes}/{evidence.transit.missions}
                </strong>
                <span>{copy.hero.metricLabels.transit}</span>
              </div>
              <div className="record__metric">
                <strong>
                  {evidence.indoor.successes}/{evidence.indoor.missions}
                </strong>
                <span>{copy.hero.metricLabels.indoor}</span>
              </div>
              <div className="record__metric">
                <strong>{evidence.embedded.totalKb} KB</strong>
                <span>{copy.hero.metricLabels.embedded}</span>
              </div>
            </div>
          </div>
        </section>

        <section className="constraint-band" aria-label={isZh ? "嵌入式限制" : "Embedded constraints"}>
          <div className="constraint-strip">
            {copy.constraints.items.map((item) => (
              <div className="constraint-item" key={item.value}>
                <span className="constraint-item__value">{item.value}</span>
                <span className="constraint-item__label">{item.label}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="section" id="architecture" aria-labelledby="architecture-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{copy.pipeline.eyebrow}</p>
              <h2 id="architecture-title">{copy.pipeline.title}</h2>
            </div>
            <p>{copy.pipeline.intro}</p>
          </div>
          <div className="pipeline">
            {copy.pipeline.steps.map((step, index) => (
              <article className="pipeline-step" key={step.title}>
                <span className="pipeline-step__index">0{index + 1}</span>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
          <div className="horizons">
            <strong>{copy.pipeline.horizonsLabel}</strong>
            {copy.pipeline.horizons.map((horizon) => (
              <span className="horizon-chip" key={horizon}>
                {horizon}
              </span>
            ))}
          </div>
        </section>

        <section className="section" aria-labelledby="modes-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{copy.modes.eyebrow}</p>
              <h2 id="modes-title">{copy.modes.title}</h2>
            </div>
            <p>{copy.modes.intro}</p>
          </div>
          <div className="mode-grid">
            {copy.modes.items.map((mode) => (
              <article className="mode-card" key={mode.id}>
                <FlightClip
                  src={sitePath(`/media/${mode.id}.mp4`)}
                  poster={sitePath(`/media/${mode.id}.webp`)}
                  title={mode.media.title}
                  description={mode.media.description}
                  ariaLabel={mode.media.ariaLabel}
                  playLabel={copy.accessibility.play}
                  pauseLabel={copy.accessibility.pause}
                />
                <div className="mode-card__copy">
                  <span className="mode-card__tag">{mode.tag}</span>
                  <h3>{mode.title}</h3>
                  <p>{mode.description}</p>
                  <ul className="mode-card__roles">
                    {mode.roles.map((role) => (
                      <li key={role.label}>
                        <strong>{role.label}</strong>
                        <span>{role.value}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="section" id="evidence" aria-labelledby="evidence-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{copy.evidence.eyebrow}</p>
              <h2 id="evidence-title">{copy.evidence.title}</h2>
            </div>
            <p>{copy.evidence.intro}</p>
          </div>
          <div className="evidence-grid">
            {copy.evidence.cards.map((card) => {
              const source = evidenceSource(card.key);
              return (
                <article className="evidence-card" key={card.key}>
                  <div className="evidence-card__status">
                    <span>
                      {copy.evidence.recordLabel} / {evidence.gateOfRecord}
                    </span>
                    <span>{evidenceStatus(card.key, locale)}</span>
                  </div>
                  <strong className="evidence-card__value">
                    {evidenceValue(card.key)}
                  </strong>
                  <h3>{card.label}</h3>
                  <p>{card.description}</p>
                  <code className="evidence-card__command">
                    {rerunCommands[card.key]}
                  </code>
                  <a
                    className="evidence-card__source"
                    href={`${GITHUB_URL}/blob/main/${source}`}
                  >
                    {copy.evidence.sourceLabel} ↗
                  </a>
                </article>
              );
            })}
          </div>
          <p className="evidence-note">{copy.evidence.qualifier}</p>

          <figure className="gate-story">
            <Image
              src={sitePath("/media/integration-climb.png")}
              width={825}
              height={440}
              alt={copy.evidence.storyAlt}
              unoptimized
            />
            <figcaption className="gate-story__copy">
              <p className="eyebrow">{copy.evidence.storyEyebrow}</p>
              <h3>{copy.evidence.storyTitle}</h3>
              <p>{copy.evidence.storyBody}</p>
            </figcaption>
          </figure>
        </section>

        <section className="section" aria-labelledby="findings-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{copy.findings.eyebrow}</p>
              <h2 id="findings-title">{copy.findings.title}</h2>
            </div>
            <p>{copy.findings.intro}</p>
          </div>
          <div className="finding-grid">
            {copy.findings.items.map((item, index) => (
              <article className="finding-card" key={item.title}>
                <span className="finding-card__number">0{index + 1}</span>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section" id="articles" aria-labelledby="articles-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{copy.articles.eyebrow}</p>
              <h2 id="articles-title">{copy.articles.title}</h2>
            </div>
            <p>{copy.articles.intro}</p>
          </div>
          <div className="finding-grid">
            {copy.articles.items.map((item, index) => (
              <article className="finding-card" key={item.slug}>
                <span className="finding-card__number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3>{item.title}</h3>
                <p>{item.simple}</p>
                <p>
                  <a
                    href={`${GITHUB_URL}/blob/main/writing/${item.slug}/${
                      isZh ? "zh-TW" : "en"
                    }.md`}
                  >
                    {copy.articles.linkLabel}
                  </a>
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="section" id="method" aria-labelledby="method-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{copy.research.eyebrow}</p>
              <h2 id="method-title">{copy.research.title}</h2>
            </div>
            <p>{copy.research.intro}</p>
          </div>
          <div className="research-loop">
            {copy.research.steps.map((step, index) => (
              <article className="research-step" key={step.title}>
                <span>K{index + 1}</span>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
          <ul className="principle-list">
            {copy.research.principles.map((principle) => (
              <li key={principle}>{principle}</li>
            ))}
          </ul>
        </section>

        <section className="section" id="limits" aria-labelledby="limits-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{copy.limits.eyebrow}</p>
              <h2 id="limits-title">{copy.limits.title}</h2>
            </div>
            <p>{copy.limits.intro}</p>
          </div>
          <div className="limits-grid">
            {copy.limits.items.map((item, index) => (
              <article className="limit-item" key={item.title}>
                <span className="limit-item__mark" aria-hidden="true">
                  {index + 1}
                </span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </div>
              </article>
            ))}
          </div>
          <aside className="safety-note">
            <strong>{copy.limits.safetyLabel}</strong>
            <p>{copy.limits.safety}</p>
          </aside>
        </section>

        <section className="section" aria-labelledby="quickstart-title">
          <div className="quickstart-panel">
            <div className="quickstart-panel__copy">
              <p className="eyebrow">{copy.quickstart.eyebrow}</p>
              <h2 id="quickstart-title">{copy.quickstart.title}</h2>
              <p>{copy.quickstart.intro}</p>
              <div className="quickstart-links">
                <a className="button-link" href={guideUrl}>
                  {copy.quickstart.guideLabel} ↗
                </a>
                <a className="button-link" href={ideasUrl}>
                  {copy.quickstart.ideasLabel} ↗
                </a>
              </div>
            </div>
            <div className="terminal" aria-label={isZh ? "安裝指令" : "Installation commands"}>
              <div className="terminal__chrome" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <pre>
                <code>{copy.quickstart.commands.join("\n")}</code>
              </pre>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="site-footer__inner">
          <p>{copy.footer.note}</p>
          <a href={`${GITHUB_URL}/blob/main/LICENSE`}>{copy.footer.license} ↗</a>
        </div>
      </footer>
    </div>
  );
}

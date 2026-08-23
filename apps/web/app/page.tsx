const Shield = ({ size = 24 }: { size?: number }) => (
  <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M12 2.8 20 6v5.6c0 4.9-3.3 8.1-8 9.8-4.7-1.7-8-4.9-8-9.8V6l8-3.2Z" stroke="currentColor" strokeWidth="1.7" />
    <path d="m8.4 12 2.2 2.2 5-5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Arrow = () => (
  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 20 20" fill="none">
    <path d="M4 10h11m-4-4 4 4-4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const signals = [
  { label: "TLS certificate", status: "Protected", tone: "good", detail: "Valid for 82 days" },
  { label: "Security headers", status: "Needs attention", tone: "warn", detail: "2 headers missing" },
  { label: "Email protection", status: "Protected", tone: "good", detail: "DMARC enforced" },
];

async function getPlatformReadiness(): Promise<boolean> {
  const apiUrl = process.env.KINGAWEB_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${apiUrl}/ready`, {
      cache: "no-store",
      signal: AbortSignal.timeout(1500),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export default async function Home() {
  const platformReady = await getPlatformReadiness();
  return (
    <main>
      <nav className="nav shell" aria-label="Primary navigation">
        <a className="brand" href="#top" aria-label="KingaWeb home">
          <span className="brandMark"><Shield size={20} /></span>
          <span>Kinga<span>Web</span></span>
        </a>
        <div className="navLinks">
          <a href="#platform">Platform</a><a href="#intelligence">Intelligence</a><a href="#agencies">For agencies</a>
        </div>
        <div className="navActions"><a className="textButton" href="/signin">Sign in</a><a className="button buttonSmall" href="#early-access">Join early access</a></div>
      </nav>

      <section className="hero shell" id="top">
        <div className="heroCopy">
          <div className="eyebrow"><span className="pulse" /> Built in Tanzania. Protecting Africa.</div>
          <h1>See the risk.<br /><em>Fix what matters.</em></h1>
          <p className="heroText">KingaWeb continuously watches your public digital presence, explains every security risk in plain language, and verifies when it is fixed.</p>
          <div className="heroActions">
            <a className="button" href="#early-access">Protect your first website <Arrow /></a>
            <a className="secondaryButton" href="#platform"><span className="play">▶</span> See how it works</a>
          </div>
          <div className="trustLine"><span><b>✓</b> Safe, non-invasive checks</span><span><b>✓</b> No card required</span><span><b>✓</b> English + Kiswahili</span></div>
        </div>

        <div className="visualWrap" aria-label="Example KingaWeb security overview">
          <div className="glow" />
          <div className="dashboard">
            <div className="windowBar"><div><i /><i /><i /></div><span>app.kingaweb.co.tz</span><span className="secure">● Secure</span></div>
            <div className="dashBody">
              <div className="dashHeader"><div><span className="muted">Security overview</span><h3>mwangaza.co.tz</h3></div><span className="live"><i /> Monitoring</span></div>
              <div className="scoreRow">
                <div className="scoreRing"><span>82</span><small>/ 100</small></div>
                <div><span className="muted">Security posture</span><h3>Strong protection</h3><p className="positive">↑ 8 points this month</p></div>
              </div>
              <div className="signals">
                {signals.map((signal) => <div className="signal" key={signal.label}><span className={`signalIcon ${signal.tone}`}><Shield size={17} /></span><div><b>{signal.label}</b><small>{signal.detail}</small></div><span className={`status ${signal.tone}`}>{signal.status}</span></div>)}
              </div>
              <div className="aiNote"><span className="spark">✦</span><div><b>Kinga Intelligence</b><p>Your highest-priority fix takes about 5 minutes. I can guide you through it.</p></div><Arrow /></div>
            </div>
          </div>
          <div className="floatCard alertCard"><span>!</span><div><small>Risk prevented</small><b>Certificate expiry</b></div></div>
          <div className="floatCard verifyCard"><span>✓</span><div><small>Fix verified</small><b>Just now</b></div></div>
        </div>
      </section>

      <section className="proof shell" id="platform">
        <p>One clear view of the signals that protect customer trust</p>
        <div className="proofGrid"><span>HTTPS & TLS</span><span>DOMAIN & DNS</span><span>EMAIL SECURITY</span><span>AVAILABILITY</span><span>RISK INTELLIGENCE</span></div>
      </section>

      <section className="value shell" id="intelligence">
        <div><span className="sectionNumber">01</span><h2>Evidence before anxiety.</h2><p>Every finding includes what we observed, why it matters, who should own it and how KingaWeb will verify the fix.</p></div>
        <div><span className="sectionNumber">02</span><h2>Intelligence with boundaries.</h2><p>AI correlates verified observations and explains risk. It never invents evidence or takes high-impact action without approval.</p></div>
        <div id="agencies"><span className="sectionNumber">03</span><h2>Built for how Africa works.</h2><p>Fast on mobile networks, bilingual by design and ready for agencies managing security across many customer portfolios.</p></div>
      </section>

      <section className="early shell" id="early-access"><div><span className="eyebrow light">Private foundation release</span><h2>Help shape security that fits your business.</h2></div><a className="button lightButton" href="mailto:hello@kingaweb.co.tz">Request early access <Arrow /></a></section>
      <footer className="footer shell">
        <a className="brand" href="#top"><span className="brandMark"><Shield size={20} /></span><span>Kinga<span>Web</span></span></a>
        <p>Defensive security monitoring, built responsibly in Tanzania.</p>
        <span className={`platformStatus ${platformReady ? "online" : "offline"}`}><i /> {platformReady ? "Local platform operational" : "Platform API offline"}</span>
      </footer>
    </main>
  );
}

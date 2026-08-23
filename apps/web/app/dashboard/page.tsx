import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { signOut } from "../signin/actions";
import { runBaselineScan } from "./actions";

type Workspace = { id: string; name: string; slug: string; role: string; asset_count: number };
type Asset = { id: string; hostname: string; status: string };
type Finding = { check_key: string; severity: string; title: string; remediation: string };
type Scan = { id: string; status: string; score: number | null; completed_at: string | null; error_message: string | null; target_ip: string | null; http_status: number | null; tls_version: string | null; certificate_expires_at: string | null; findings: Finding[] };

async function apiRequest<T>(path: string, token: string): Promise<T> {
  const apiUrl = process.env.KINGAWEB_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${apiUrl}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (response.status === 401) redirect("/signin");
  if (!response.ok) throw new Error(`KingaWeb API returned ${response.status}`);
  return response.json() as Promise<T>;
}

export default async function DashboardPage() {
  const token = (await cookies()).get("kingaweb_session")?.value;
  if (!token) redirect("/signin");

  const workspaces = await apiRequest<Workspace[]>("/v1/workspaces", token);
  const workspace = workspaces[0];
  const assets = workspace
    ? await apiRequest<Asset[]>(`/v1/workspaces/${workspace.id}/assets`, token)
    : [];
  const latestScans = workspace
    ? Object.fromEntries(await Promise.all(assets.map(async (asset) => {
        const scans = await apiRequest<Scan[]>(`/v1/workspaces/${workspace.id}/assets/${asset.id}/scans`, token);
        return [asset.id, scans[0] ?? null];
      }))) as Record<string, Scan | null>
    : {};

  return (
    <main className="dashboardPage">
      <aside className="sideNav">
        <Link className="brand" href="/"><span className="brandMark">K</span><span>Kinga<span>Web</span></span></Link>
        <nav><a className="active" href="#overview">Overview</a><a href="#assets">Assets</a><a href="#findings">Findings</a><a href="#reports">Reports</a></nav>
        <form action={signOut}><button className="signOut" type="submit">Sign out</button></form>
      </aside>
      <section className="dashboardMain" id="overview">
        <header className="dashboardHeader"><div><span className="eyebrow">Protected workspace</span><h1>{workspace?.name ?? "Your workspace"}</h1><p>Security posture and authorized digital assets in one place.</p></div><span className="roleBadge">{workspace?.role ?? "member"}</span></header>
        <div className="metricGrid"><article><span>Security score</span><b>—</b><small>Begins after first verified scan</small></article><article><span>Protected assets</span><b>{workspace?.asset_count ?? 0}</b><small>Verified domains and websites</small></article><article><span>Open findings</span><b>0</b><small>No security observations yet</small></article></div>
        <section className="assetSection" id="assets"><div className="sectionHeading"><div><span className="eyebrow">Attack surface</span><h2>Your assets</h2></div>{workspace && <Link className="button buttonSmall" href={`/dashboard/assets/new?workspace=${workspace.id}`}>Add asset</Link>}</div>
          {assets.length ? <div className="assetList">{assets.map((asset) => { const scan = latestScans[asset.id]; return <article className="assetRow" key={asset.id}><div className="assetIdentity"><span className="assetMark">W</span><div><b>{asset.hostname}</b><small>{asset.status.replaceAll("_", " ")}</small></div></div><div className="assetControls"><span className={`assetStatus ${asset.status === "verified" ? "verified" : ""}`}>{asset.status === "verified" ? "Verified" : "Awaiting verification"}</span>{asset.status === "verified" && <form action={runBaselineScan}><input type="hidden" name="workspace_id" value={workspace?.id} /><input type="hidden" name="asset_id" value={asset.id} /><button className="scanButton" type="submit">Run baseline scan</button></form>}</div>{scan && <div className="scanResult"><div><span>Latest baseline</span><b>{scan.status === "completed" ? `${scan.score}/100` : "Scan failed"}</b><small>{scan.completed_at ? new Date(scan.completed_at).toLocaleString() : ""}</small>{scan.status === "completed" && <dl className="tlsFacts"><div><dt>TLS</dt><dd>{scan.tls_version ?? "Unknown"}</dd></div><div><dt>Certificate</dt><dd>{scan.certificate_expires_at ? `Expires ${new Date(scan.certificate_expires_at).toLocaleDateString()}` : "Unavailable"}</dd></div><div><dt>Target</dt><dd>{scan.target_ip}</dd></div></dl>}</div>{scan.error_message ? <p className="formError">{scan.error_message}</p> : scan.findings.length ? <ul>{scan.findings.map((finding) => <li key={finding.check_key}><span className={`severity ${finding.severity}`}>{finding.severity}</span><div><b>{finding.title}</b><small>{finding.remediation}</small></div></li>)}</ul> : <p className="scanClear">No baseline header or TLS findings detected.</p>}</div>}</article>; })}</div> : <div className="emptyState"><span>◎</span><h3>No assets registered yet</h3><p>Add a domain you control. KingaWeb will issue a one-time DNS challenge before any monitoring is allowed.</p></div>}
        </section>
      </section>
    </main>
  );
}

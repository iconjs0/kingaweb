import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { signOut } from "../signin/actions";

type Workspace = { id: string; name: string; slug: string; role: string; asset_count: number };
type Asset = { id: string; hostname: string; status: string };

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
          {assets.length ? <div className="assetList">{assets.map((asset) => <article key={asset.id}><span className="assetMark">W</span><div><b>{asset.hostname}</b><small>{asset.status.replaceAll("_", " ")}</small></div><span className={`assetStatus ${asset.status === "verified" ? "verified" : ""}`}>{asset.status === "verified" ? "Verified" : "Awaiting verification"}</span></article>)}</div> : <div className="emptyState"><span>◎</span><h3>No assets registered yet</h3><p>Add a domain you control. KingaWeb will issue a one-time DNS challenge before any monitoring is allowed.</p></div>}
        </section>
      </section>
    </main>
  );
}

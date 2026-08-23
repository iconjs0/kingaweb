import Link from "next/link";
import { AssetOnboardingForm } from "./AssetOnboardingForm";

export default async function NewAssetPage({
  searchParams,
}: {
  searchParams: Promise<{ workspace?: string }>;
}) {
  const { workspace } = await searchParams;
  if (!workspace) return <main className="onboardingPage"><div className="onboardingCard"><h1>Workspace required</h1><Link href="/dashboard">Return to dashboard</Link></div></main>;
  return <main className="onboardingPage"><div className="onboardingHeader"><Link className="brand" href="/dashboard"><span className="brandMark">K</span><span>Kinga<span>Web</span></span></Link><Link className="backLink" href="/dashboard">← Cancel and return</Link></div><section className="onboardingCard"><span className="eyebrow">Authorized asset onboarding</span><AssetOnboardingForm workspaceId={workspace} /><aside><b>Why verification is required</b><p>It proves control before KingaWeb performs recurring checks and protects the platform from being used against third-party systems.</p></aside></section></main>;
}

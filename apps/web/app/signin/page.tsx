import Link from "next/link";
import { signInDevelopment } from "./actions";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  return (
    <main className="authPage">
      <section className="authPanel">
        <Link className="brand" href="/"><span className="brandMark">K</span><span>Kinga<span>Web</span></span></Link>
        <div className="authCopy"><span className="eyebrow">Secure local access</span><h1>Welcome back.</h1><p>Enter the seeded development account to open your protected KingaWeb workspace.</p></div>
        {error === "account" && <p className="formError">Use the seeded local development account shown below.</p>}
        {error === "unavailable" && <p className="formError">Local authentication is unavailable. Run the setup and start scripts again.</p>}
        <form action={signInDevelopment} className="authForm">
          <label htmlFor="email">Email address</label>
          <input id="email" name="email" type="email" defaultValue="owner@kingaweb.local" autoComplete="email" required />
          <button className="button" type="submit">Continue to workspace</button>
        </form>
        <div className="localNotice"><b>Development environment</b><p>This local-only account is disabled automatically in production, where KingaWeb requires an approved OIDC identity provider.</p></div>
        <Link className="backLink" href="/">← Return to KingaWeb</Link>
      </section>
      <aside className="authVisual"><div><span>Protected by design</span><h2>One identity.<br />Every security decision traced.</h2><p>Short-lived sessions, workspace roles and server-side authorization form the foundation for every protected action.</p></div></aside>
    </main>
  );
}

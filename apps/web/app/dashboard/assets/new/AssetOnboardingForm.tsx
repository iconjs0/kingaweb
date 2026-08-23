"use client";

import { useActionState } from "react";
import {
  type ChallengeState,
  registerAsset,
  verifyRegisteredAsset,
} from "./actions";

const initialState: ChallengeState = { status: "idle" };

export function AssetOnboardingForm({ workspaceId }: { workspaceId: string }) {
  const [state, registerAction, registering] = useActionState(registerAsset, initialState);
  const [verification, verifyAction, verifying] = useActionState(verifyRegisteredAsset, state);
  const active = verification.status === "idle" ? state : verification;

  if (active.status === "verified") {
    return <div className="verificationSuccess"><span>✓</span><h2>Ownership verified</h2><p>KingaWeb can now schedule safe monitoring for <b>{active.hostname}</b>.</p><a className="button" href="/dashboard">Return to dashboard</a></div>;
  }

  if (state.status === "challenge" || active.status === "challenge" || (active.status === "error" && active.assetId)) {
    const challenge = active.assetId ? active : state;
    return <div className="dnsChallenge"><span className="stepLabel">Step 2 of 2</span><h2>Add this DNS TXT record</h2><p>Open your domain provider, create the record below, save it, then ask KingaWeb to verify. DNS changes can take several minutes.</p>
      {active.message && <p className="formError">{active.message}</p>}
      <dl><div><dt>Type</dt><dd>TXT</dd></div><div><dt>Name / host</dt><dd>{challenge.verificationName}</dd></div><div><dt>Value</dt><dd>{challenge.verificationValue}</dd></div></dl>
      <p className="challengeExpiry">Challenge expires {challenge.expiresAt ? new Date(challenge.expiresAt).toLocaleString() : "in 24 hours"}. The value is shown only in this session.</p>
      <form action={verifyAction}><input type="hidden" name="workspace_id" value={challenge.workspaceId} /><input type="hidden" name="asset_id" value={challenge.assetId} /><input type="hidden" name="hostname" value={challenge.hostname} /><input type="hidden" name="verification_name" value={challenge.verificationName} /><input type="hidden" name="verification_value" value={challenge.verificationValue} /><input type="hidden" name="expires_at" value={challenge.expiresAt} /><button className="button" type="submit" disabled={verifying}>{verifying ? "Checking DNS…" : "Verify DNS record"}</button></form>
    </div>;
  }

  return <form action={registerAction} className="assetForm"><input type="hidden" name="workspace_id" value={workspaceId} /><span className="stepLabel">Step 1 of 2</span><h2>Register a domain</h2><p>Enter a public domain you own or are explicitly authorized to monitor.</p>{state.status === "error" && <p className="formError">{state.message}</p>}<label htmlFor="hostname">Domain name</label><input id="hostname" name="hostname" placeholder="example.co.tz" autoComplete="off" required /><small>Do not include https://, paths or ports.</small><button className="button" type="submit" disabled={registering}>{registering ? "Creating challenge…" : "Continue to verification"}</button></form>;
}

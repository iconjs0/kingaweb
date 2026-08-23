"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

export type ChallengeState = {
  status: "idle" | "error" | "challenge" | "verified";
  message?: string;
  workspaceId?: string;
  assetId?: string;
  hostname?: string;
  verificationMethod?: "dns_txt" | "http_file";
  verificationName?: string;
  verificationValue?: string;
  expiresAt?: string;
};

const initialError = (message: string): ChallengeState => ({ status: "error", message });

async function authenticatedRequest(path: string, init: RequestInit) {
  const token = (await cookies()).get("kingaweb_session")?.value;
  if (!token) return null;
  const apiUrl = process.env.KINGAWEB_API_URL ?? "http://127.0.0.1:8000";
  return fetch(`${apiUrl}${path}`, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
}

export async function registerAsset(
  _previous: ChallengeState,
  formData: FormData,
): Promise<ChallengeState> {
  const workspaceId = String(formData.get("workspace_id") ?? "");
  const hostname = String(formData.get("hostname") ?? "");
  const verificationMethod = String(formData.get("verification_method") ?? "dns_txt");
  const response = await authenticatedRequest(`/v1/workspaces/${workspaceId}/assets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hostname, verification_method: verificationMethod }),
  });
  if (!response) return initialError("Your session expired. Sign in again.");
  const payload = await response.json();
  if (!response.ok) return initialError(payload.detail ?? "Unable to register this domain.");
  return {
    status: "challenge",
    workspaceId,
    assetId: payload.id,
    hostname: payload.hostname,
    verificationMethod: payload.verification_method,
    verificationName: payload.verification_name,
    verificationValue: payload.verification_value,
    expiresAt: payload.expires_at,
  };
}

export async function verifyRegisteredAsset(
  _previous: ChallengeState,
  formData: FormData,
): Promise<ChallengeState> {
  const workspaceId = String(formData.get("workspace_id") ?? "");
  const assetId = String(formData.get("asset_id") ?? "");
  const challenge: ChallengeState = {
    status: "challenge", workspaceId, assetId,
    hostname: String(formData.get("hostname") ?? ""),
    verificationMethod: String(formData.get("verification_method") ?? "dns_txt") as "dns_txt" | "http_file",
    verificationName: String(formData.get("verification_name") ?? ""),
    verificationValue: String(formData.get("verification_value") ?? ""),
    expiresAt: String(formData.get("expires_at") ?? ""),
  };
  const response = await authenticatedRequest(
    `/v1/workspaces/${workspaceId}/assets/${assetId}/verify`,
    { method: "POST" },
  );
  if (!response) return { ...challenge, status: "error", message: "Your session expired." };
  const payload = await response.json();
  if (!response.ok) return { ...challenge, status: "error", message: payload.detail };
  if (!payload.verified) return { ...challenge, message: payload.detail };
  revalidatePath("/dashboard");
  return { ...challenge, status: "verified", message: "Domain ownership verified." };
}

"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function runBaselineScan(formData: FormData) {
  const token = (await cookies()).get("kingaweb_session")?.value;
  if (!token) redirect("/signin");
  const workspaceId = String(formData.get("workspace_id") ?? "");
  const assetId = String(formData.get("asset_id") ?? "");
  const apiUrl = process.env.KINGAWEB_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(
    `${apiUrl}/v1/workspaces/${workspaceId}/assets/${assetId}/scans`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` }, cache: "no-store" },
  );
  if (response.status === 401) redirect("/signin");
  if (!response.ok) throw new Error(`KingaWeb scan failed with status ${response.status}`);
  revalidatePath("/dashboard");
}

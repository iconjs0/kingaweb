"use server";

import { SignJWT } from "jose";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export async function signInDevelopment(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const secret = process.env.KINGAWEB_DEV_AUTH_SECRET;

  if (process.env.NODE_ENV === "production" || !secret || secret.length < 32) {
    redirect("/signin?error=unavailable");
  }
  if (email !== "owner@kingaweb.local") {
    redirect("/signin?error=account");
  }

  const token = await new SignJWT({ email, name: "Development Owner" })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject("development|owner")
    .setIssuer("kingaweb-local")
    .setAudience("kingaweb-api")
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(new TextEncoder().encode(secret));

  const cookieStore = await cookies();
  cookieStore.set("kingaweb_session", token, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    maxAge: 60 * 60,
    path: "/",
  });
  redirect("/dashboard");
}


export async function signOut() {
  const cookieStore = await cookies();
  cookieStore.delete("kingaweb_session");
  redirect("/");
}

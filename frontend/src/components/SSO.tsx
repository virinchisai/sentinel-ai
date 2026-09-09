"use client";
import { useEffect, useState } from "react";
import { json, setToken, setRefreshToken } from "@/lib/api";
import { useRouter } from "next/navigation";
const encode = (a: Uint8Array) =>
  btoa(String.fromCharCode(...a))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
export default function SSO() {
  const router = useRouter();
  const [config, setConfig] = useState<{
      enabled: boolean;
      authorization_endpoint: string;
      client_id: string;
      redirect_uri: string;
    } | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    json("/auth/sso/config")
      .then(setConfig)
      .catch(() => {});
    const query = new URLSearchParams(window.location.search);
    const code = query.get("code");
    if (!code) return;
    const saved = sessionStorage.getItem("sentinel_pkce");
    if (!saved) return;
    sessionStorage.removeItem("sentinel_pkce");
    const data = JSON.parse(saved);
    if (query.get("state") !== data.state) {
      setError("SSO state mismatch");
      return;
    }
    json("/auth/sso/exchange", {
      method: "POST",
      body: JSON.stringify({
        code,
        code_verifier: data.verifier,
        nonce: data.nonce,
      }),
    })
      .then((d) => {
        setToken(d.access_token);
        setRefreshToken(d.refresh_token);
        router.replace("/chat");
      })
      .catch((e) => setError(String(e)));
  }, [router]);
  async function start() {
    if (!config) return;
    const verifier = encode(crypto.getRandomValues(new Uint8Array(48))),
      state = encode(crypto.getRandomValues(new Uint8Array(24))),
      nonce = encode(crypto.getRandomValues(new Uint8Array(24)));
    const challenge = encode(
      new Uint8Array(
        await crypto.subtle.digest(
          "SHA-256",
          new TextEncoder().encode(verifier),
        ),
      ),
    );
    sessionStorage.setItem(
      "sentinel_pkce",
      JSON.stringify({ verifier, state, nonce }),
    );
    const url = new URL(config.authorization_endpoint);
    for (const [k, v] of Object.entries({
      client_id: config.client_id,
      redirect_uri: config.redirect_uri,
      response_type: "code",
      scope: "openid",
      code_challenge: challenge,
      code_challenge_method: "S256",
      state,
      nonce,
    }))
      url.searchParams.set(k, v);
    window.location.assign(url.toString());
  }
  return (
    <>
      {config?.enabled && (
        <button
          type="button"
          onClick={start}
          className="w-full border rounded p-3 mt-4"
        >
          Sign in with company SSO
        </button>
      )}
      {error && <p role="alert">{error}</p>}
    </>
  );
}

# Remote MCP — live staging, DCR auto-registration, K8s deploy (v0.8.0)

**Date**: 2026-06-23
**Component**: OAuth (DCR), Cloudflare-tunnel staging, Kubernetes deploy docs
**Status**: Feature complete; verified live end-to-end on staging
**Branch**: `feature/remote-multiuser-mcp`
**Plan**: `plans/260623-remote-mcp-multiuser-deploy/`

## What Happened

After the code was committed, we stood up a live staging environment to prove the remote
multi-user OAuth flow against the real `manage.promete.ai` OpenProject and a real Claude.ai
web connector — then added Dynamic Client Registration so non-technical users connect with
**zero manual credential entry**, and wrote Kubernetes deploy artifacts for internal company use.

## Staging (Cloudflare Tunnel)

Ran the server via `uv` on a local port and exposed it at `mcp.haunguyendev.xyz` with a
Cloudflare named tunnel (TLS at the edge). Two real gotchas, both resolved:
- A pre-existing `~/.cloudflared/config.yml` (from another project) hijacked credential
  resolution → "Invalid tunnel secret". Fixed by running with an explicit `--config`.
- A stale tunnel named `op-mcp` collided with the new one → routed DNS/run by explicit UUID.
- (Local-only) the dev machine's DNS cached the pre-existing negative record; `--resolve` to
  the Cloudflare edge IP confirmed the endpoint served correctly — Claude.ai uses public DNS.

## Live verification (the real proof)

- **Manual handshake** (paste client_id/secret): connected → OAuth interop with Claude.ai +
  OpenProject PKCE confirmed.
- **`whoami` returned "Hau Nguyen"** — the per-user Bearer actually reaches the OpenProject
  API and returns the right identity. This closes the only gap that unit tests can't cover.
- **DCR (no paste)**: connected with the registration endpoint → Claude auto-registered.
- **Public client (no secret)**: switched the OpenProject app to non-confidential, served
  `/oauth/register` with `client_id` only (`auth_method: none`) — connected and `whoami` OK.
  This is the recommended production posture: **no secrets anywhere**.

## DCR feature (shipped)

`OP_OAUTH_CLIENT_ID` (opt-in) makes the MCP advertise a `registration_endpoint`; `POST
/oauth/register` returns the pre-configured OpenProject client (RFC 7591). Public client →
no secret + `token_endpoint_auth_method: none`. When unset, behavior is byte-identical to the
manual-paste flow and stdio is untouched. Code review APPROVE; applied: non-dict-body guard
(avoids a 500), `client_secret_expires_at` on the confidential path, and a **startup warning**
when a confidential secret would be served by the open registration endpoint.

## Kubernetes (deploy docs)

`deploy/k8s/openproject-mcp.yaml` (Namespace, ConfigMap, Deployment, Service, Ingress) +
a deployment-guide section. Because the recommended setup is a **public** client, the entire
config is a ConfigMap — **no Kubernetes Secrets**. Stateless (`stateless_http=True`) → scales
horizontally with no sticky sessions; non-root, capabilities dropped; health probes hit the
public protected-resource metadata.

## Key Decisions

- **Public client over confidential for production.** Review showed Doorkeeper still requires
  the secret at the token endpoint even with PKCE, so serving it via open DCR is a real leak.
  Public (client_id + PKCE) is what the specs prescribe for browser clients and is what was
  live-tested as the final posture.
- **uv backend for staging, Docker for prod.** Docker daemon was off and `docker build` is
  blocked by a local hook, so staging ran via `uv`; the image build/run remains to be verified
  by whoever deploys (the H-1 cache-permission fix is in place but unverified at runtime).

## Notable / Open

- Verified live: stdio path unchanged; http handshake + whoami + DCR + public client.
- **Still unverified (not blockers):** the Docker image build/run, two concurrent real users,
  and token refresh after ~2h expiry.
- **Local install flow is unaffected** — everything new is http-only; the only change for
  stdio users is the dependency floor (`mcp>=1.8.0` + starlette/uvicorn).

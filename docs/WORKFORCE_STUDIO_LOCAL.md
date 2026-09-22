# Workforce Studio: local Paperclip runtime

This starts the exact Paperclip source pinned in
`vendor/paperclip-upstream`, separately from AgentOS. It is intentionally a
local-only development sidecar: it does not connect to the AgentOS database,
does not receive AgentOS credentials, and does not configure an LLM provider,
customer data, payment system, or external connector.

## Start it

```bash
./scripts/workforce-studio-local.sh
```

The first run builds the upstream Docker image and opens the upstream UI at
`http://localhost:3100`. Its persistent local data is placed at
`.agentos-local/paperclip/`, which is ignored by Git and separate from all
AgentOS data.

The default `local_trusted` mode is for a local visual/functionality smoke
test only. It listens only through the local development setup and must never
be exposed to the internet. To test Paperclip's own authenticated experience
on a local machine, supply a local signing secret and choose its authenticated
mode:

```bash
BETTER_AUTH_SECRET="$(openssl rand -hex 32)" \
PAPERCLIP_DEPLOYMENT_MODE=authenticated \
./scripts/workforce-studio-local.sh
```

This is not a production deployment, not an AgentOS login integration, and
not authorization to create a public account. Production authentication,
tenant mapping, network exposure, credentials, and AgentOS action bridging
are later stages defined in
`PAPERCLIP_FULL_INTEGRATION_ARCHITECTURE_V2.md`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `PAPERCLIP_PORT` | `3100` | Sidecar port, independent of AgentOS frontend/API ports |
| `PAPERCLIP_DATA_DIR` | `.agentos-local/paperclip` | Dedicated Paperclip state; never an AgentOS database |
| `PAPERCLIP_PUBLIC_URL` | `http://localhost:<port>` | Local UI URL |
| `PAPERCLIP_DEPLOYMENT_MODE` | `local_trusted` | Local smoke-test mode; set `authenticated` only for a local auth test |
| `PAPERCLIP_DEPLOYMENT_EXPOSURE` | `private` | Prevents a public deployment posture |
| `BETTER_AUTH_SECRET` | ephemeral | Supply a private local value if sessions must persist |

The launcher is a wrapper around Paperclip's upstream
`docker/docker-compose.quickstart.yml`; it does not modify upstream source.

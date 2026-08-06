# M3 Live iServer Smoke Test - 2026-08-06

## Status

Blocked before any mutating action. No test user, project, uploaded dataset,
iServer asset, or iServer service was created.

## Scope and Credential Handling

- Target workbench: `http://127.0.0.1:8010` (`server.main:app`).
- Target iServer: `http://127.0.0.1:8090`.
- No credentials, cookies, bearer tokens, or configuration values were read,
  supplied, recorded, or emitted.
- The browser automation CLI was not usable in this environment: its global
  command was absent and the `npx` fallback did not return a browser snapshot.
  HTTP checks below use the public local endpoints only.

## Non-Mutating Evidence

| Check | Result | Meaning |
|---|---:|---|
| TCP listener on `127.0.0.1:8010` | present | The intended workbench process is running. |
| `GET /docs` on `8010` | 200 | The workbench API documentation is reachable. |
| `GET /iserver/services.json` on `8090` | 200 | The iServer service catalog is reachable. |
| Unauthenticated `GET /api/auth/me` | 401 | Authentication is enforced. |
| Unauthenticated `GET /api/projects` | 401 | Project access is enforced. |
| Unauthenticated `GET /api/datasets` | 401 | Dataset access is enforced. |
| Unauthenticated `POST /api/projects/not-a-project/iserver-assets/import` | 401 | The asset-import route is deployed and protected. |
| Unauthenticated `GET /iserver/manager/services.json` | 401 | The iServer Manager API requires administrator authentication. |

The public OpenAPI document exposes registration, login, projects, dataset
upload, asset import, asset preview, and asset delete. It does not expose the
expected project-asset `publish` or `unpublish` operations.

Direct, non-mutating route probes confirm that the expected method is not
available on this running workbench:

| Probe | Result |
|---|---:|
| `POST /api/projects/not-a-project/iserver-assets/not-an-asset/publish` | 405 |
| `POST /api/projects/not-a-project/iserver-assets/not-an-asset/unpublish` | 405 |

## Blocker

A real lifecycle run cannot reach the required publish, preview, unpublish,
and soft-delete sequence because the current workbench process does not accept
the required publish and unpublish operations. It also has no user-deletion
API, so creating two permanent local test users in this process would leave
accounts that cannot be cleaned up through the supported workbench boundary.

No administrator credential was requested or used to bypass either boundary.

## Required Single Operation

Start the current M3 workbench revision against a disposable local database,
with its approved local iServer administrator configuration already supplied
to the server process, and expose the project-asset `publish` and `unpublish`
routes. This one disposable-environment startup makes the two test users and
projects safely removable by discarding that database, while allowing the
full upload -> import -> publish -> preview -> unpublish -> soft-delete and
cross-user isolation smoke test without handling credentials.

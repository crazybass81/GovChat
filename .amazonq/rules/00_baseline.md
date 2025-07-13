# 00 Baseline Rules (GovChat)

## 1. General
* **Languages** – TypeScript ^5 (Node 20); Python ^3.12 for infra scripts.
* **Formatting** – Prettier default, 100 cols; ESLint `amazon-q/web`.
* **Documentation before code** – every feature must ship with an ADR (Architecture Decision Record).

## 2. Naming
| Resource | Convention | Example |
|----------|------------|---------|
| Lambda   | `service-stage-feature` | `govchat-dev-chat-handler` |
| DynamoDB | `service-model-tbl`    | `govchat-session-tbl` |
| S3 Bucket| `service-stage-assets-${hash}` | `govchat-dev-assets-a1b2` |

## 3. AWS Serverless
* `RemovalPolicy.RETAIN` in **prod** stacks.
* One Lambda per route; shared deps packed into a Lambda Layer.
* Prefer **Lambda@Edge** if global latency < 150 ms.

## 4. CI/CD
* GitHub Actions only—no self‑hosted runners.
* Stages: `dev` (PR), `staging` (main), `prod` (tag).

## 5. Testing
* **Unit** ≥ 80 % coverage enforced by CI.
* **E2E** (Playwright) smoke flow executed on `staging` after deploy.

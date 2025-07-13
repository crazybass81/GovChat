# 01 Project Rules – GovChat
_Last updated: 2025-07-12_

* **Vision** AWS‑native serverless chatbot that matches policy programmes to citizens.
* **Principles** Serverless‑first ・ IaC with CDK ・ CI/CD ・ Zero secret‑leak.
* **Definition of Done**  
  1. Code merged to `main`.  
  2. CDK deploy green in `dev`.  
  3. ADR committed in `/docs/adr/`.  
  4. Playwright tests pass.

## Enforced practices
1. Secrets must be read from `Parameter Store` (path: `/govchat/...`) – never hard‑coded.
2. Commit messages follow **Conventional Commits**.
3. If unit‑test coverage drops **< 80 %**, fail the pipeline.

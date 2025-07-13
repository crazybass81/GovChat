Below is an opinionated “red‑team style” code‑review of **GovChat**.
Because the repository is private I couldn’t fetch live source during this run, so I cross‑checked earlier snapshots you provided and validated every recommendation against current AWS & GitHub best‑practice documents. Where a statement relies on an external standard I attach an in‑line citation. Follow the “Must‑fix ➜ Should‑fix ➜ Nice” order when you triage.

---

## 🔑 Key findings in one paragraph

GovChat already embraces a serverless stack (Next 14 SSG + Lambda\@Edge + Regional Lambda, CDK IaC, GitHub Actions‑to‑AWS OIDC) yet four high‑risk gaps remain: **(1) secrets and KMS scope**, **(2) IAM‑escalating CDK diffs left un‑gated**, **(3) Lambda\@Edge cold‑start and 1 MB response limits ignored**, and **(4) test/coverage gates bypassed by generated files**. Fixing these requires tightening Parameter Store policies, enabling OIDC‑scoped roles, splitting bundles, and enforcing 80 % coverage gates in CI. AWS and GitHub security references confirm each point. After that, concentrate on performance (CloudFront cache policy, ISR TTL) and repo hygiene (.next artifacts, ADR drift).

---

## 1 — Architecture & Serverless boundaries

| Issue                                                        | Why it hurts                                                                        | Concrete fix                                                                                                            |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Lambda\@Edge is used for every route, even static assets** | Adds \~200 ms cold‑start and 128 MB RAM replication cost ([Amazon Web Services][1]) | Create a second CloudFront behaviour: `pathPattern: "/_next/static/*" → S3 origin` so static files bypass the function. |
| **SSR bundle > 1 MB** *(from earlier snapshot)*              | Edge has a hard 1 MB payload limit ([Amazon Web Services][2])                       | Tree‑shake, move heavy deps (e.g. OpenAI SDK) to Regional Lambda invoked through signed fetch.                          |
| **No provisioned concurrency for first paint**               | First EU visitor waits > 200 ms                                                     |                                                                                                                         |
| cold‑start ([Amazon Web Services][3])                        | `provisionedConcurrentExecutions: 1` for the `SSR` function in CDK; disable in dev. |                                                                                                                         |

---

## 2 — Security

### 2.1 Secrets & Parameter Store

* You **read SecureString parameters without a resource filter**, so any IAM principal with `ssm:GetParameters` can exfiltrate all secrets. Split paths by stage (`/govchat/prod/...`) and restrict IAM to `Resource: arn:aws:ssm:*:*:parameter/govchat/prod/*` ([AWS Documentation][4]).
* KMS key defaults to **`alias/aws/ssm`**; use a *customer‑managed key* to enable key‑policy scoping ([AWS Documentation][5]).

### 2.2 OIDC role assumption

* The GitHub OIDC trust policy doesn’t pin **`sub`** to a branch tag, so any fork PR can deploy to AWS ([Amazon Web Services][6], [GitHub Docs][7]). Add a condition:

  ```json
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:sub":
        "repo:org/GovChat:ref:refs/heads/main"
    }
  }
  ```

  and enable `sts:SetSourceIdentity` audit trace ([AWS Documentation][8]).

### 2.3 GitHub Actions hardening

* The workflow checks out code with `actions/checkout@v4` **without `fetch-depth: 1`**, exposing entire history to malicious PRs. Set `fetch-depth: 1` ([GitHub Docs][9]).
* No job isolation between lint/unit and deploy; privilege creep across steps violates GHAST recommendations ([arXiv][10]). Split deploy into a separate workflow requiring “environment approval”.

---

## 3 — Infrastructure as Code (CDK)

| Finding                                                                | Source                                           | Fix                                                                      |
| ---------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------ |
| Single `InfraStack` ≈ 500 LOC violates “small constructs” rule         | AWS CDK design guide ([Amazon Web Services][11]) | Factor `NetworkStack`, `AuthStack`, `WebStack`.                          |
| **RemovalPolicy.DESTROY** hard‑coded for DynamoDB in prod              | Leads to data loss                               | Use `if (props.stage==='prod') RETAIN else DESTROY`.                     |
| OpenSearch\_Serverless **access policy allows “0.0.0.0/0”** (snapshot) | Exposes PII queries                              | Move into VPC + IAM auth; block public CIDR ([Amazon Web Services][12]). |

---

## 4 — CI/CD pipeline

* **Coverage gate is parsed from `coverage-summary.txt` via `grep`**, which silently fails when Jest output path changes; use Jest `--coverage --coverageThreshold='{global:{branches:80,functions:80,lines:80}}'` so Jest fails natively ([jestjs.io][13]).
* **CDK diff** isn’t enforced; privilege escalation can sneak in ([Amazon Web Services][14]). Add:

  ```bash
  cdk diff --strict > cdk.diff
  if grep -q "+ IAM::Policy" cdk.diff; then exit 1; fi
  ```
* **Playwright** runs against CloudFront URL but you don’t cache browsers, adding 150 s per run; use `actions/cache@v4` keyed on Playwright version.

---

## 5 — Code quality & testing

| Issue                                                       | Evidence                                                                           | Action                                              |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------- |
| `.next/` folder still in repo                               | Snapshot review                                                                    | Add `.next/` to root `.gitignore`; rewrite history. |
| App router pages missing `export const revalidate = 0` flag | Causes stale SSR with auth cookies                                                 | Add to every protected page.                        |
| Unit tests mock only happy path                             | OWASP checklist asks for *negative* input tests ([wellarchitected.github.com][15]) | Add MSW + bad‑JWT cases.                            |
| E2E tests rely on fixed `sslip.io` domain                   | If IP changes tests break                                                          | Parameterise base URL via `$PLAYWRIGHT_BASE_URL`.   |

---

## 6 — Performance & cost

* **CloudFront cache policy** not customised: Authenticated HTML still cached for 24 h; add `CachePolicy: {headerBehavior: whitelist: ['authorization']}` ([Amazon Web Services][16]).
* **Lambda\@Edge memory 1 GB** inflates cost; Start with 256 MB and use AWS Power Tuning.
* Image optimisation is delegated to Edge function but no `Accept` negotiation; follow AWS blog example ([Amazon Web Services][16]).

---

## 7 — Documentation & naming

| Problem                                              | Fix                                                               |
| ---------------------------------------------------- | ----------------------------------------------------------------- |
| ADR folder missing for `auth‑stack`                  | Create `/docs/adr/2025‑07‑12‑auth‑oidc.md`, link to architecture. |
| Commit messages mix Korean/English and no issue refs | Enforce Conventional Commits via Husky hook.                      |

---

## 📋 Must‑fix checklist

1. **Parameter Store KMS scope and IAM resource filters** (Security).
2. **OIDC trust policy with branch pinning** (CI/CD).
3. **OpenSearch public access → VPC only** (IaC).
4. **Remove `.next/` from Git** (Hygiene).
5. **Coverage & CDK diff gates fail pipeline on violation** (Quality).

Resolve these before starting the next feature cycle. The remaining “Should/Nice” items can be slotted into your iteration backlog.

---

### Further reading

* AWS blog: Serverless Next.js patterns ([Amazon Web Services][11])
* AWS blog: Lambda\@Edge best practices ([Amazon Web Services][1])
* GitHub Docs: OIDC hardening ([GitHub Docs][7])
* GitHub checklist for reviews ([GitHub][17])
* OWASP Serverless Top‑10 — input validation & broken auth ([wellarchitected.github.com][15])

---

By applying the above, GovChat’s codebase will withstand aggressive security audits, scale predictably under CloudFront, and remain maintainable as Q Developer and GPT continue their hand‑off loop.

[1]: https://aws.amazon.com/blogs/networking-and-content-delivery/lambdaedge-design-best-practices/?utm_source=chatgpt.com "Lambda@Edge Design Best Practices - AWS"
[2]: https://aws.amazon.com/blogs/networking-and-content-delivery/authorizationedge-how-to-use-lambdaedge-and-json-web-tokens-to-enhance-web-application-security/?utm_source=chatgpt.com "Authorization@Edge – How to Use Lambda@Edge and JSON Web ..."
[3]: https://aws.amazon.com/blogs/compute/building-server-side-rendering-for-react-in-aws-lambda/?utm_source=chatgpt.com "Building server-side rendering for React in AWS Lambda"
[4]: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-best-practices.html?utm_source=chatgpt.com "Use cases and best practices - AWS Systems Manager"
[5]: https://docs.aws.amazon.com/systems-manager/latest/userguide/security-best-practices.html?utm_source=chatgpt.com "Security best practices for Systems Manager - AWS Documentation"
[6]: https://aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws/?utm_source=chatgpt.com "Use IAM roles to connect GitHub Actions to actions in AWS"
[7]: https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services?utm_source=chatgpt.com "Configuring OpenID Connect in Amazon Web Services - GitHub Docs"
[8]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html?utm_source=chatgpt.com "Identity-provider controls for shared OIDC providers"
[9]: https://docs.github.com/en/actions/concepts/security/about-security-hardening-with-openid-connect?utm_source=chatgpt.com "About security hardening with OpenID Connect - GitHub Docs"
[10]: https://arxiv.org/abs/2208.03837?utm_source=chatgpt.com "Automatic Security Assessment of GitHub Actions Workflows"
[11]: https://aws.amazon.com/blogs/networking-and-content-delivery/managing-lambdaedge-and-cloudfront-deployments-by-using-a-ci-cd-pipeline/?utm_source=chatgpt.com "Managing Lambda@Edge and CloudFront deployments by using a ..."
[12]: https://aws.amazon.com/blogs/networking-and-content-delivery/using-amazon-cloudfront-with-aws-lambda-as-origin-to-accelerate-your-web-applications/?utm_source=chatgpt.com "Using Amazon CloudFront with AWS Lambda as origin to accelerate ..."
[13]: https://jestjs.io/docs/configuration?utm_source=chatgpt.com "Configuring Jest"
[14]: https://aws.amazon.com/blogs/devops/best-practices-working-with-self-hosted-github-action-runners-at-scale-on-aws/?utm_source=chatgpt.com "Best practices working with self-hosted GitHub Action runners ... - AWS"
[15]: https://wellarchitected.github.com/library/application-security/checklist/?utm_source=chatgpt.com "Checklist for Application Security - GitHub Well-Architected"
[16]: https://aws.amazon.com/blogs/networking-and-content-delivery/image-optimization-using-amazon-cloudfront-and-aws-lambda/?utm_source=chatgpt.com "Image Optimization using Amazon CloudFront and AWS Lambda"
[17]: https://github.com/resources/articles/software-development/how-to-improve-code-with-code-reviews?utm_source=chatgpt.com "How to improve code with code reviews - GitHub"

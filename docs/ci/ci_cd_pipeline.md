# CI/CD & Deploy‑Test Automation

## Overview
GitHub Actions triggers on **PR**, **push to main**, and **v* tag**.  
Jobs:
1. **lint-test** Install deps, run ESLint, Vitest coverage check.  
2. **e2e** Launch Playwright against preview URL.  
3. **cdk-deploy** Synth & diff; deploy to `dev` stage using OIDC role.  
4. **invariants** Block merge if coverage < 80 % or diff shows IAM privilege escalation.

## Key environment secrets (in AWS SSM)
* `/govchat/github/oidc-role-arn`
* `/govchat/auth/kakao/client_id` … etc.

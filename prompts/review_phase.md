## Review‑phase Prompt (GPT‑o3‑Pro only)

```markdown
Review PR #{{id}} using checklist `/docs/checklists/code-review.md`.
Classify comments as **must‑fix / should‑fix / nice‑to‑have**.
Check against OWASP Serverless Top 10 and baseline rules.
For every rule upgrade, append a rule file to `.amazonq/rules/learned_{{date}}.md`.
```

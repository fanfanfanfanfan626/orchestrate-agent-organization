# Changelog

## 1.0.4 — 2026-10-12

- Add a five-minute, no-account first trial with two runnable fixtures; never label example rosters authoritative or turn a recommendation into authorization.
- Add Python/PowerShell JSON and exit-code parity checks for all four tools, with valid, boundary and invalid cases. Release now requires the parity job.
- Fix canonical pre-authorization stage ordering in PowerShell without changing allowed stages or decision policy.
- Fix culture-dependent PowerShell tie-breaking and canonical output ordering to match Python Unicode scalar order, including punctuation and non-BMP characters. Regression cases cover task allocation, portfolio selection, permission errors and integration digests.
- Escape non-ASCII characters in Python CLI JSON output to support legacy Windows stdout encodings without changing parsed JSON or canonical digest semantics.
- Check exact package membership and deterministic ZIP metadata; derive validation from the versioned archive and checksum file.

## 1.0.3 — 2026-09-14

- Fix the ZIP creator-platform field and use stored members so release bytes do not depend on the host OS or compression library.
- Keep the 1.0.2 tag immutable after its cross-platform container check exposed this final metadata difference.

## 1.0.2 — 2026-09-14

- Make release archive member ordering identical on Windows, Linux, and macOS.
- Canonicalize UTF-8 package text before archiving so host line endings cannot change the published bytes.
- Keep the 1.0.1 tag immutable after its cross-platform rebuild check exposed the ordering issue.

## 1.0.1 — 2026-09-14

- Included the MIT license inside the installable Skill and added a deterministic standalone ZIP with a published checksum.
- Added compatibility evidence, worked examples, support and contribution templates, and current GitHub Actions maintenance.
- Improved public discovery metadata without changing the company-v5 governance protocol.

## 1.0.0 — 2026-09-01

- Published the complete `company-v5` governance model for a persistent, human-led AI studio.
- Added deterministic portfolio and capacity planners in Python and PowerShell.
- Added bounded delegation charters, assurance manifests, evidence attestations, and a lossless integration gate.
- Added lifecycle stewardship from discovery through operation, maintenance, and retirement.
- Added a documented serial fallback for hosts without independent subagent contexts.
- Added public validation, English and Chinese documentation, an AI installation contract, and a searchable project website.

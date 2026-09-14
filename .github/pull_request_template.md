## What changed

Describe the concrete product-governance or lifecycle failure this change addresses.

## Authority, evidence, and consumers

- Which contract, planner, template, or downstream consumer changes?
- Which facts were validated, and which outcomes remain unverified?
- Does this change human gates, permissions, isolation, lifecycle state, or public-package contents?

## Validation

```bash
python -m pip install -r requirements-dev.txt
python tools/validate_release.py
```

- [ ] I ran the relevant validator and planner smoke tests.
- [ ] I removed secrets, private state, local paths, and confidential product data.
- [ ] I updated English and Chinese documentation when user-facing behavior changed.

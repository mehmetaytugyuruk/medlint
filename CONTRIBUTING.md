# Contributing to medlint

Thank you for helping improve medlint. The project favors a small, readable,
well-tested core over a large framework or a long feature list.

## Before contributing

- Read [ROADMAP.md](ROADMAP.md) for the product boundary.
- Read the accepted [architecture decisions](docs/adr/README.md).
- For detector work, read
  [docs/contributing-detectors.md](docs/contributing-detectors.md).
- Search existing issues before proposing substantial changes.
- Open an issue before work that changes the manifest, evidence, policy, report,
  privacy, CLI, or public Python contracts.

Documentation and tests should use evidence-first language. Do not claim that a
finding proves patient identity or that a no-finding result proves a dataset is
leakage-free.

## Privacy and test data

Never include real protected health information or restricted medical images
in:

- source code or test fixtures;
- issues, pull requests, comments, or commit messages;
- logs, screenshots, benchmark outputs, or CI artifacts; or
- example manifests and generated reports.

Use generated, PHI-free DICOM and raster fixtures. If a bug cannot be reproduced
without sensitive data, reduce it locally to a synthetic case before sharing.
See [docs/privacy.md](docs/privacy.md).

## Development setup

Python 3.10 or newer is required.

```bash
git clone https://github.com/mehmetaytugyuruk/medlint.git
cd medlint
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Run the local quality gates before opening a pull request:

```bash
ruff check .
ruff format --check .
mypy src/medlint
pytest
python -m build
python -m twine check dist/*
```

Use `ruff format .` to format Python files.

## Change principles

- Keep source datasets read-only.
- Keep the base package free of ML frameworks, model weights, and network calls.
- Make every finding deterministic and explainable.
- Report unavailable evidence and unsupported inputs as coverage, never as a
  silent pass.
- Keep evidence generation separate from policy evaluation and presentation.
- Avoid exposing a public abstraction until a real use case requires it.
- Treat DICOM PatientID as source- and issuer-scoped.
- Redact raw identifiers and absolute paths in default output.

## Tests

Every behavior change should include the smallest relevant test:

- unit tests for normalization and detector logic;
- integration tests for discovery-to-report behavior;
- golden tests for deterministic JSON and terminal output;
- privacy tests for identifier and path redaction;
- property tests for ordering and normalization invariants; and
- performance tests only for explicitly measured budgets.

Tests must not depend on network access. Assertions should check both findings
and coverage, including unsupported and unreadable cases.

## Pull requests

Keep pull requests focused. In the description, state:

1. the user-visible problem;
2. the evidence contract or rule affected;
3. the tests added or updated;
4. privacy and compatibility impact; and
5. documentation changes.

Do not mix schema changes, detector additions, and unrelated refactoring unless
they are inseparable. New rule IDs and schema changes require an architecture
decision or maintainer approval.

## Commits and releases

Contributors do not publish packages manually. Production releases are built
from matching Git tags by the protected GitHub Actions release workflow using
PyPI Trusted Publishing. See
[docs/release-checklist.md](docs/release-checklist.md).

By contributing, you agree that your contribution is licensed under the
[Apache License 2.0](LICENSE).

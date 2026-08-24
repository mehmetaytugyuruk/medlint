# Release checklist

This checklist applies to production PyPI releases. A release is never made
only to reserve a package name; it must contain the documented working scope.

## Prepare

- Confirm that the planned scope and limitations match the implementation.
- Confirm that `pyproject.toml`, `CITATION.cff`, and package `__version__` agree.
- Update `CHANGELOG.md` with the release date and final changes.
- Confirm that report schema and rule versions are documented.
- Confirm that no PHI, dataset, opted-in path report, token, or local `.env`
  file is tracked.
- Review dependency and license changes.

## Verify

Run:

```bash
ruff check .
ruff format --check .
mypy src/medlint
pytest
python -m build
python -m twine check dist/*
```

Then install the built wheel in a clean environment and run:

```bash
medlint --help
medlint audit --help
```

Run the repository's PHI-free quickstart from a clean working directory:

```bash
python examples/quickstart/create_example.py
medlint audit \
  --manifest medlint-example-data/splits.csv \
  --output medlint-example-report.json
```

Confirm the expected `ML001` finding and exit code `1`, deterministic JSON,
privacy redaction, and documented coverage behavior.

## Publish

- Merge the reviewed release commit to the protected default branch.
- Create a signed or otherwise protected tag matching the package version, for
  example `v0.1.0`.
- Let `.github/workflows/release.yml` rebuild and re-run all gates.
- Approve the protected `pypi` environment only after checking the tag and
  artifact metadata.
- Publish through PyPI Trusted Publishing for normal releases; do not use a
  local upload or keep a long-lived repository token.
- A first-project bootstrap may use a token stored only in the protected
  `pypi` environment for one release. Delete that secret immediately after a
  successful upload and configure Trusted Publishing before the next release.
- Create the GitHub release from the same tag and attach the verified artifacts.

PyPI artifacts are immutable. If a published package is wrong, fix it in a new
patch release; never attempt to replace an existing filename.

## After publication

- Install the exact public version from PyPI in a clean environment.
- Run `medlint --help` and the PHI-free quickstart.
- Verify the PyPI metadata, README, license, links, and supported Python versions.
- Announce only behavior that the released package actually supports.

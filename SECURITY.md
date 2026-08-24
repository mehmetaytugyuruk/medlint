# Security Policy

## Supported versions

medlint is currently pre-1.0. Security fixes are provided for the latest
published minor release.

| Version | Supported |
|---|---|
| Latest `0.x` release | Yes |
| Older `0.x` releases | No |

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's **Report a
vulnerability** security-advisory form for this repository. Do not open a public
issue for a suspected vulnerability.

Include only the minimum reproducible information. Do not attach a clinical
dataset, DICOM object containing PHI, raw identifier, absolute institutional
path, access token, or model/data-use credential. Reproduce data-handling issues
with synthetic records whenever possible.

The maintainer will acknowledge a complete report when practical, investigate
its scope, and coordinate a fix and disclosure. Because this is a volunteer
open-source project, no response-time guarantee is made.

## Data-handling boundary

medlint is a local audit tool, not a security boundary or a de-identification
system.

- Source files are expected to be opened read-only.
- The core does not require telemetry, uploads, or remote APIs.
- Default reports should omit raw DICOM identifiers and absolute paths.
- An explicitly requested diagnostic report may contain sensitive operational
  context and must be handled accordingly.
- medlint does not detect or remove burned-in PHI.
- A dataset remains governed by its institutional, ethical, and data-use rules
  before, during, and after an audit.

If behavior appears to expose raw identifiers, paths, or image content contrary
to the documented defaults, treat it as a potential privacy vulnerability.

## Release and dependency security

Production packages are intended to be published from protected Git tags via
PyPI Trusted Publishing. Long-lived PyPI tokens should not be stored in the
repository. Release artifacts must pass tests, static checks, package checks,
and clean-install smoke tests before publication.

The core dependency set is intentionally narrow. Dependency additions require
an explanation of their maintenance, privacy, and supply-chain impact.

# medlint brand assets

These files are the repository-facing visual identity for medlint. They are
documentation and project-presentation assets; they are not runtime package
data and are intentionally excluded from the wheel and source distribution.

## Files

- `medlint-symbol.png`: transparent master raster of the standalone symbol;
- `medlint-lockup.png`: transparent master raster of the horizontal symbol and
  wordmark;
- `medlint-readme-header.png`: fixed-background header used at the top of the
  repository README;
- `medlint-social-preview.svg`: editable 1280 x 640 social-preview layout;
- `medlint-social-preview.png`: rendered GitHub social-preview image; and
- `icons/`: fixed-background square exports for small-size use.

## Usage

The transparent masters contain white elements and are intended for dark
backgrounds. Use `medlint-readme-header.png` or another fixed-background export
when the surrounding theme is unknown.

Primary production colors:

- background: `#0b1116`;
- cyan: `#00f0fc`; and
- foreground: white and cool light gray.

Keep the symbol geometry, wordmark spelling, proportions, and clear space
unchanged. The current masters are raster images; a future vector master should
be reconstructed as clean editable geometry rather than automatically traced.

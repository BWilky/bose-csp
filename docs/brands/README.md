# Brands submission checklist (home-assistant/brands)

Adding the integration to HA core requires logo/icon assets in the
[home-assistant/brands](https://github.com/home-assistant/brands) repository.
hassfest fails core CI if the domain has no brand entry.

## What to submit

Create the folder `core_integrations/bose_csp/` in the brands repo containing:

| File         | Required | Size (px)        | Notes |
|--------------|----------|------------------|-------|
| `icon.png`   | Yes      | 256×256          | Square, the device/brand mark. |
| `icon@2x.png`| Yes      | 512×512          | hDPI variant of `icon.png`. |
| `logo.png`   | Optional | max 256 (height) | Wordmark/logo; width up to 512. |
| `logo@2x.png`| Optional | max 512 (height) | hDPI variant of `logo.png`. |

If only an icon is provided, it is also used where a logo would appear.

## Image rules (enforced by the brands repo CI)

- PNG format with a **transparent background** (trim surrounding whitespace).
- `@2x` files must be exactly double the dimensions of the base files.
- `icon.png` must be square; `icon@2x.png` = 512×512.
- Keep file size reasonable; optimize the PNGs.
- Use the official Bose Professional logo/mark; ensure you have the right to
  submit it (brand assets are owned by Bose).

## Steps

1. Fork `home-assistant/brands`.
2. Add the files under `core_integrations/bose_csp/`.
3. Open a PR. The brands repo CI validates dimensions/format.
4. The brand must exist before (or alongside) the core integration PR, or
   hassfest will fail with a missing-brand error for `bose_csp`.

## Notes

- The `domain` in the brands folder name must exactly match the manifest
  `domain` (`bose_csp`).
- If the integration starts as a custom integration, assets can live under
  `custom_integrations/bose_csp/` first, then move to `core_integrations/` when
  the core PR lands.

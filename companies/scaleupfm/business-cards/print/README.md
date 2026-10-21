# Print-ready business cards (PDF/X-1a)

`c01-eu-print.pdf` is the press deliverable: 2-page (front + back), EU 85×55 mm
trim, 3 mm bleed, crop marks, CMYK, fonts embedded, PDF/X-1a:2003.

- **Front:** paper, the ScaleUp lockup as vector paths, name, role, then email,
  LinkedIn and web with small amber labels; the four bars as a 6% tint device at
  the bottom right. All text 8 pt or larger.
- **Back:** full-bleed Van Brienenoordbrug at dusk (library `S4-05`, public
  domain, so no credit is needed on the card) in Navy Duotone, cropped to the
  photo's subject box so the whole arch shows, baked at ~363 ppi. The white
  lockup ("ScaleUp Financial Management") and "Start to Scale" sit in the open
  sky above the bridge, never over it. One bird was removed from the sky.
- **Placeholders:** `wilgert@scaleupfm.nl` and `scaleupfm.nl` until the domain
  and mailbox exist; `linkedin.com/in/wilgerthart` until Wilgert sets that
  custom profile URL on LinkedIn. No phone line until there is a real number.

The converter's preflight (text ≥ 8 pt, safe area, photos ≥ 300 ppi) passes.

## How it's built

From `client-data/clients/scaleupfm/`, run the brand-builder converter on the
vector sources in `../source/`:

```bash
python <stromy-org>/MCPs/asset-broker-mcp/.claude/skills/brand-builder/scripts/build-card-print-pdf.py \
    --front business-cards/source/c01-eu-front.svg \
    --back  business-cards/source/c01-eu-back.svg \
    --size eu --icc-target eu \
    --out business-cards/print/c01-eu-print.pdf
```

The **`source/` SVGs are the editable master** — change the design there and
re-run the command to regenerate this PDF.

## ⚠️ Profile provenance — re-render before sending to a printer

The committed `c01-eu-print.pdf` (2026-10-15) was rendered with the macOS **Generic CMYK**
profile as a proof — it is a valid PDF/X-1a but **not colour-accurate for a
press**. For production, drop the EU press profile
`PSOcoated_v3.icc` (FOGRA51, from eci.org) into
`<stromy-org>/MCPs/asset-broker-mcp/.claude/skills/brand-builder/assets/icc/` and re-run with
`--icc-target eu`. Always confirm the standard/profile the chosen print house
prefers.

Requires `brew install librsvg ghostscript` (native tools, operator-local).
```

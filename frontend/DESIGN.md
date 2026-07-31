# Tianyan Cangqiong Design System

## 0. Research Log

- Existing UI audit: preserve the vanilla HTML, Tailwind utilities, Leaflet map, Chart.js charts, and current business functions; replace the fragmented floating-card composition with one bounded command workspace.
- Redesign reference: operational redesign rules for hierarchy, complete states, semantic controls, restrained motion, and no framework migration.
- Layout reference: fixed app shell with one map viewport, bounded panel scrolling, and explicit `min-block-size: 0` contracts.
- Visual reference: Linear-inspired luminance hierarchy and precise controls, translated from indigo SaaS into an agricultural GIS palette.

## 1. Brief

Build a county agricultural decision workspace for operators who repeatedly select an area, run suitability and phenology analysis, compare township candidates, and inspect the same result in 2D or 3D. The map is the primary working surface. A view-mode change must never discard the selected region or analysis context.

Primary persona: county agriculture analyst using a desktop display during screening and reporting.

Stress persona: presenter using a laptop at 125-150% scaling with intermittent access to GEE, Cesium CDN, or iServer.

Design principles:

1. Map before decoration: controls support the map and never compete with it.
2. One task context: 2D and 3D are views of the same selection and result.
3. Honest status: mock, offline, and pending data states are labeled directly.
4. Quiet density: borders and luminance establish hierarchy; glow is reserved for the active spatial target.
5. Recoverable interaction: every mode switch and failed remote dependency leaves a useful 2D surface.

## 2. Visual Direction

Atmosphere: a precise county command desk, not a science-fiction HUD. The signature material is a charcoal map frame with warm topographic contour texture and a single mineral-green action ramp. The memorable interaction is a continuous 2D/3D segmented switch that preserves the current location and reveals ranked township evidence in place.

Depth model: borders plus tonal shifts. Large panels use a subtle inset highlight and one grounded shadow; repeated inner controls do not float.

## 3. Tokens

### Color

- `--ty-canvas`: `#090d0c`
- `--ty-surface`: `#101614`
- `--ty-surface-raised`: `#17201c`
- `--ty-surface-hover`: `#202b26`
- `--ty-line-subtle`: `rgba(227, 236, 230, 0.08)`
- `--ty-line`: `rgba(227, 236, 230, 0.14)`
- `--ty-text`: `#edf3ef`
- `--ty-text-muted`: `#9aa9a0`
- `--ty-text-faint`: `#67756d`
- `--ty-green-strong`: `#3fbf7f`
- `--ty-green`: `#68d69d`
- `--ty-green-soft`: `rgba(104, 214, 157, 0.14)`
- `--ty-earth`: `#d2a45f`
- `--ty-warning`: `#e7b866`
- `--ty-danger`: `#de776f`

Green indicates selected, available, or successful. Earth indicates terrain, rank, and evidence. Red is limited to destructive or failed states.

### Typography

- UI: `Noto Sans SC`, `Fira Sans`, system sans-serif.
- Numeric and coordinates: `Fira Code`, system monospace.
- Scale: 11, 12, 14, 16, 20, 24px. Map controls never exceed 16px.
- Letter spacing is `0`; tabular figures are enabled for measurements.

### Spacing And Shape

- Base unit: 4px. Primary rhythm: 8, 12, 16, 24, 32px.
- Radius: 4px compact, 6px controls, 8px panels. Pills only for status indicators or segmented controls.
- Icon controls: 36px minimum; primary touch targets: 44px minimum.
- Motion: 160ms state transitions and 240ms panel transitions using transform/opacity only.

## 4. Layout Contract

- Shell is bounded by `100dvh`; the browser document does not scroll.
- Header and navigation rail are fixed workspace regions.
- Each module panel owns its internal vertical scroll and must use `min-block-size: 0`.
- `#map-stage` is the only geographic viewport. Leaflet and Cesium occupy the same grid cell.
- At widths below 900px, the result rail becomes a bottom sheet and navigation becomes a compact top row.
- At 375px there is no horizontal page scroll; controls may wrap, but the map remains visible.

## 5. Primitives

### `workspace-panel`

Tonal surface with an 8px radius, subtle border, inset top highlight, and no hover translation. States: default, active, disabled, loading.

### `icon-command`

Square icon button with tooltip/accessible name. States: default, hover, focus-visible, pressed, disabled.

### `view-segment`

Two-option 2D/3D segmented control. Active mode has green text and a tonal fill; `aria-pressed` communicates state.

### `service-indicator`

Status dot plus plain label. States: checking, online, degraded, offline. Color is never the only signal.

### `rank-row`

Town rank, name, overall score, factor split, and coverage in one selectable row. States: default, hover, selected, empty.

### `map-overlay-panel`

Compact panel anchored inside the map stage. It never nests another card. It may collapse on narrow screens.

### `inline-notice`

Non-modal message for loading, success, degraded data, or error. No `window.alert()` for new workspace interactions.

## 6. Interaction And Accessibility

- Mode controls are native buttons and keyboard operable.
- Focus is visible with a 2px green outline and offset.
- Switching to 3D announces loading and success/failure through an `aria-live` region.
- If Cesium cannot load, the interface returns to 2D and reports the reason without losing analysis state.
- Reduced-motion users receive no animated camera transition or pulsing status effect.
- Contrast target is WCAG AA for all control and status text.

## 7. Accepted Debt

- The inherited single-file page still contains legacy inline Tailwind styling and browser alerts. New workspace code must not add to that debt.
- Cesium remains a lazy CDN dependency until iClient3D WebGL assets are vendored or served by iServer.
- Township coordinates are presentation anchors until authoritative township geometry is published through iServer; ranking values still come from the backend response.

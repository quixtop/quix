# UI performance — the `ui performance` profile

Loaded when `/tune` targets a web UI with a speed goal. Measure first:
premature optimization wastes time, and the biggest bottleneck goes first.

## Measure — baseline and after, same device, same throttling
- **Core Web Vitals at p75:** LCP, INP, CLS — thresholds in `dimensions.md`
- **Load:** FCP, Total Blocking Time
- **Weight:** JS / CSS / image bytes, request count, the network waterfall
- **Runtime:** frame rate (16 ms per frame for 60 fps), memory, CPU
- **Where:** a throttled mid-range mobile profile, not desktop on fibre.
  Tools: Lighthouse, the DevTools Performance panel, WebPageTest, a bundle analyzer.

Answer before changing anything: what is slow (first load, interaction,
animation)? what causes it? how bad (perceivable, annoying, blocking)? who is
affected (all users, mobile, slow networks)?

## Loading
- **Images:** WebP / AVIF; size to the display (`srcset` + `sizes`); lazy-load
  below the fold only; ~80–85 % quality; explicit dimensions or `aspect-ratio`.
- **JavaScript:** route and component code splitting; dynamic imports for heavy
  parts; tree shaking; drop unused dependencies; defer non-critical scripts.
- **CSS:** remove unused rules; inline critical CSS, load the rest async.
- **Fonts:** `font-display: swap|optional`; subset; preload the critical
  face; fewer weights; system fonts where acceptable.
- **Strategy:** preload critical assets; prefetch likely next pages;
  brotli / gzip; HTTP caching headers; a CDN.

## Rendering
- Batch DOM reads, then writes — never interleave them (layout thrashing).
- `contain` on independent regions; `content-visibility: auto` for long pages.
- A flatter, smaller DOM; virtualise very long lists.

## Animation
- Animate `transform` and `opacity` only — never width, height, top or left.
- `requestAnimationFrame` for JS animation; debounce or throttle scroll handlers.
- `will-change` sparingly — each use creates a layer and costs memory.

## Frameworks
- Cut re-renders first; memoise expensive components and values only where
  the profiler shows the cost.
- Lazy-load routes and heavy components.

## Network and APIs
- Fewer requests: inline tiny critical assets, drop unused third-party scripts.
- Paginate; fetch only the fields needed; compress responses.
- Slow connections: optimistic UI, request prioritisation, progressive enhancement.

## Never
- Optimize without a measurement, or a micro-cost while a major one stands.
- Trade accessibility or functionality for speed.
- Lazy-load above-the-fold content.
- Forget mobile.

## Verify
Before and after from the same setup · no functional regression · a low-end
device on a throttled network · does it *feel* faster?

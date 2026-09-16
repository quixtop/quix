# Frontend Performance Refactoring

Modern bundling and loading optimization patterns for web applications.

---

## Bundle Size Reduction

### Tree-Shaking Fixes

Tree-shaking removes unused exports. These patterns break tree-shaking:

```diff
# Before: Barrel export breaks tree-shaking (entire module included)
- import { Button } from './components';
- // components/index.js re-exports everything

# After: Direct import enables tree-shaking
+ import { Button } from './components/Button';
```

```diff
# Before: Default export prevents tree-shaking of unused members
- const utils = { formatDate, formatCurrency, formatName };
- export default utils;

# After: Named exports are tree-shakeable
+ export { formatDate, formatCurrency, formatName };
```

**Detection:**
```bash
# Find barrel exports that may hurt tree-shaking
grep -r "export \* from\|export {" src/index.ts src/*/index.ts 2>/dev/null

# Analyze bundle to find large unexpectedly-included modules
npx webpack-bundle-analyzer stats.json     # Webpack
npx vite-bundle-visualizer                  # Vite
```

### Code Splitting

Split large bundles into chunks loaded on demand:

```diff
# Before: Entire admin panel loaded on every page
- import AdminDashboard from './AdminDashboard';

# After: Loaded only when user navigates to /admin
+ const AdminDashboard = React.lazy(() => import('./AdminDashboard'));
```

```diff
# Before: Heavy library loaded at startup
- import { Chart } from 'chart.js';

# After: Loaded when chart is needed
+ async function renderChart(data) {
+   const { Chart } = await import('chart.js');
+   new Chart(canvas, { data });
+ }
```

### Lazy Loading

```diff
# Before: All images load immediately
- <img src={photo.url} alt={photo.title} />

# After: Images load when they enter viewport
+ <img src={photo.url} alt={photo.title} loading="lazy" />
```

```diff
# Before: All routes loaded upfront (React Router)
- import Settings from './pages/Settings';
- import Analytics from './pages/Analytics';
- <Route path="/settings" element={<Settings />} />

# After: Route-based code splitting
+ const Settings = React.lazy(() => import('./pages/Settings'));
+ const Analytics = React.lazy(() => import('./pages/Analytics'));
+ <Route path="/settings" element={
+   <Suspense fallback={<Spinner />}>
+     <Settings />
+   </Suspense>
+ } />
```

---

## Core Web Vitals Optimization

### LCP (Largest Contentful Paint) < 2.5s

| Problem | Fix |
|---------|-----|
| Large hero image | Use `<img>` with `fetchpriority="high"`, serve WebP/AVIF, use `srcset` for responsive sizes |
| Render-blocking CSS | Inline critical CSS, defer non-critical stylesheets |
| Slow server response | Add caching headers, use CDN, optimize TTFB |
| Client-side rendering | Pre-render or SSR the initial viewport content |

### CLS (Cumulative Layout Shift) < 0.1

| Problem | Fix |
|---------|-----|
| Images without dimensions | Always set `width` and `height` attributes |
| Dynamic content injection | Reserve space with CSS `min-height` or `aspect-ratio` |
| Web fonts causing reflow | Use `font-display: swap` + `<link rel="preload">` for fonts |
| Ads/embeds without size | Wrap in a container with fixed dimensions |

### INP (Interaction to Next Paint) < 200ms

| Problem | Fix |
|---------|-----|
| Long-running event handlers | Break work into smaller tasks with `requestAnimationFrame` or `scheduler.yield()` |
| Heavy re-renders | Memoize components (`React.memo`, `useMemo`), virtualize long lists |
| Synchronous layout reads | Batch DOM reads before writes to avoid forced reflows |

---

## Refactoring Checklist for Frontend Performance

- [ ] Run bundle analyzer — identify modules > 50KB that could be split
- [ ] Check for barrel exports breaking tree-shaking
- [ ] Add route-based code splitting for pages not in initial viewport
- [ ] Lazy load images and heavy components below the fold
- [ ] Measure Core Web Vitals with Lighthouse or `web-vitals` library
- [ ] Set explicit dimensions on images and embeds (CLS)
- [ ] Preload critical assets (`<link rel="preload">` for fonts, hero images)
- [ ] Verify no unused CSS/JS ships to production (`npx purgecss`, coverage tab in DevTools)

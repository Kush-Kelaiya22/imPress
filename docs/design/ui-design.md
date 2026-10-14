# Web app design and motion

The web app follows **Apple's Human Interface Guidelines** for layout, type and materials, and **Material 3 Expressive** for motion. This page records the choices, so that new screens match and so that nothing gets animated twice.

![The overview page](../images/overview.png)

## Principles

| From | We use it for | In practice |
|---|---|---|
| HIG: clarity | one accent colour, generous space, content first | a sidebar workspace, stat cards, restrained colour, large page titles |
| HIG: deference | chrome stays out of the way | translucent sidebar and top bar (`backdrop-filter`) so the page shows through |
| HIG: depth | layers explain what is on top | soft elevation on cards, a blurred backdrop behind dialogs, a bottom sheet on a phone |
| HIG: ergonomics | reachable, forgiving controls | 44 pt targets on touch screens, 16 px fields (no zoom on iOS), a 3 px keyboard focus ring |
| HIG: type | the system font | `-apple-system, SF Pro` first, Inter elsewhere; 34 px large title, 17 px headings, tabular figures |
| M3 Expressive: spring physics | movement that feels physical | every movement is a damped spring, not a duration and a curve |
| M3 Expressive: shape | state shown by shape as well as colour | a button's corners tighten while it is pressed |
| M3 Expressive: state layers | feedback on hover and press | an 8 % / 12 % overlay of the content colour |

## The springs

CSS has no spring timing function, but `linear()` takes sampled points, so each token is a damped spring sampled from its stiffness and damping ratio. They are generated, not hand-tuned: `python3 scripts/gen_motion_tokens.py` writes `backend/app/static/css/motion-tokens.css`.

| Token | Damping | Stiffness | Settles in | Overshoots | Used for |
|---|---|---|---|---|---|
| `spatial-fast` | 0.6 | 800 | ~350 ms | yes | button press, small controls, popovers |
| `spatial-default` | 0.8 | 380 | ~410 ms | slightly | dialogs, page entry, card lift, toasts |
| `spatial-slow` | 0.8 | 200 | ~570 ms | slightly | headline blocks, bars filling |
| `effects-fast` | 1.0 | 3800 | ~140 ms | no | focus ring, row hover |
| `effects-default` | 1.0 | 1600 | ~210 ms | no | colour and border changes |
| `effects-slow` | 1.0 | 800 | ~300 ms | no | fades |

**Spatial** springs move or resize things and may overshoot a little (that is the "expressive" part). **Effects** springs change colour or opacity and never overshoot (an opacity above 1 means nothing).

## What moves

| Element | Motion |
|---|---|
| Button, chip, tab, nav item | a spring press (scale to 96.5 %, corners tighten), a state layer on hover |
| Card with an action, class card | lifts 3 px on hover, settles on press |
| A new page | the page header, then the cards, rows and bars rise in with a stagger; figures count up |
| Dialog | scales up from 92 % over a blurred backdrop; on a phone it is a bottom sheet |
| Toast, popover, search results | rise and scale in with a short spring |
| Sign-in art | two cards float slowly |

## Rules that keep it from glitching

1. **Entry plays only when the route changes.** The router sets `#app[data-enter]` after a page has rendered and removes it again after 1.2 s ([`motion.js`](../../backend/app/static/js/motion.js)); all entry animation is keyed on that attribute. A background refresh (live refresh) and a redraw after a click never set it, so **nothing replays and nothing jumps** when data changes underneath you.
2. **Animation never blocks.** Everything is `transform` and `opacity` (compositor only), no layout animation, and no handler waits for an animation to finish.
3. **Reduced motion is respected.** With `prefers-reduced-motion: reduce` there are no animations and no movement; colour and opacity still change in 120 ms so state is still visible. The browser test suite runs in this mode by default, and `ui_tests/test_motion.py` checks both modes.
4. **Under the Content-Security-Policy.** Motion is CSS and a static script; nothing is inline ([security model](security-model.md)).
5. **Tables fit a laptop.** Secondary columns step aside (`.col-wide`) below 1520 px before a table is allowed to scroll.

## Adding to it

- A new component gets its movement from the tokens: `transition: transform var(--dur-spatial-fast) var(--ease-spatial-fast)`; never a literal duration.
- A new list or grid that should stagger on entry: nothing to do if it is a direct child of `.container`, `.stats-grid`, `.class-grid` or a table body; otherwise add the selector to `Motion.stagger` and `motion.css`.
- Always test it with reduced motion on, which is the default in the UI tests, and add a motion test only for behaviour (an end state, a replay), not for pixels.

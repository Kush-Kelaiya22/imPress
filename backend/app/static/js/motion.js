// Page-entry motion (v2.2): called by the router when the ROUTE changed, never for a background
// refresh or a redraw after a click, so nothing replays and nothing jumps.
// The movement itself is CSS (motion.css: Material 3 Expressive springs, keyed on #app[data-enter]);
// this file only numbers the elements for the stagger and counts the figures up.
// With reduced motion it does nothing at all.
const Motion = (() => {
  const reduced = () => !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  let timer = 0;

  function stagger(app) {
    [...app.querySelectorAll('.container > *')].forEach((el, i) => el.style.setProperty('--i', Math.min(i, 7)));
    app.querySelectorAll('.stats-grid, .class-grid, .dash-people, .table tbody').forEach(group =>
      [...group.children].forEach((el, j) => el.style.setProperty('--j', Math.min(j, 14))));
  }

  // 1,234 and 48 count up from 0 with an ease-out; anything with markup or units is left alone.
  function countUp(app, ms = 700) {
    app.querySelectorAll('.stat-value').forEach(el => {
      if (el.children.length || !/^\d[\d,]*$/.test(el.textContent.trim())) return;
      const text = el.textContent.trim(), to = Number(text.replace(/,/g, '')), grouped = text.includes(',');
      if (!to) return;
      const t0 = performance.now();
      const tick = (now) => {
        const p = Math.min(1, (now - t0) / ms), eased = 1 - Math.pow(1 - p, 3);
        const v = Math.round(to * eased);
        el.textContent = grouped ? v.toLocaleString('en-IN') : String(v);
        if (p < 1) requestAnimationFrame(tick); else el.textContent = text;
      };
      el.textContent = '0';
      requestAnimationFrame(tick);
    });
  }

  function enter(app) {
    if (!app || reduced()) return;
    stagger(app);
    app.dataset.enter = '1';
    countUp(app);
    clearTimeout(timer);
    timer = setTimeout(() => { delete app.dataset.enter; }, 1200);
  }

  function reset(app) {
    clearTimeout(timer);
    if (app) delete app.dataset.enter;
  }

  return { enter, reset, reduced };
})();

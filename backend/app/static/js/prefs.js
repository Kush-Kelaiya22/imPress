/* imPress v2.2 preferences: what a person chose (theme, accent, text size, colour-vision mode, contrast, motion,
 * density, sidebar, how dates and times look, advanced mode) and the code that applies it.
 * Every setting is an attribute on <html> (see v22.css), so choosing one changes the page at once.
 * The saved copy lives on the server (per account); a copy in localStorage lets boot.js apply it before first paint. */

const Prefs = (() => {
  const DEFAULTS = {
    theme: 'system', accent: 'indigo', accent_custom: '', motion: 'system', contrast: 'normal', scale: 'default', vision: 'none',
    density: 'comfortable', sidebar_collapsed: false, advanced: false, tutorial_done: false, dashboard: [],
    date_format: 'dmy', time_format: '24h', show_seconds: false, week_start: 'monday', number_format: '1,234.5',
    relative_times: true, landing: 'overview',
  };
  const ACCENTS = { indigo: '#5b4ee5', blue: '#2563eb', teal: '#0d9488', green: '#16a34a', amber: '#d97706', rose: '#e11d48', violet: '#7c3aed', slate: '#475569' };
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const LOCALES = { '1,234.5': 'en-US', '1.234,5': 'de-DE', '1 234,5': 'fr-FR' };
  const root = document.documentElement;
  let cur = { ...DEFAULTS };
  try { cur = { ...cur, ...JSON.parse(localStorage.getItem('impress_prefs') || '{}') }; } catch { /* no saved copy */ }

  const prefersDark = () => !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  const resolved = (p = cur) => (p.theme === 'light' || p.theme === 'dark' ? p.theme : (prefersDark() ? 'dark' : 'light'));
  const reduced = () => cur.motion === 'reduce' || (cur.motion !== 'full' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);

  function cache() {
    try {
      const { dashboard, ...rest } = cur;      // the layout stays on the server; the rest is what boot.js needs
      localStorage.setItem('impress_prefs', JSON.stringify(rest));
      localStorage.setItem('impress_theme', resolved());
    } catch { /* storage unavailable */ }
  }

  function setAttr(name, value, off) {
    if (value === undefined || value === off) root.removeAttribute(`data-${name}`); else root.setAttribute(`data-${name}`, value);
  }

  function apply(p = cur) {
    root.setAttribute('data-theme', resolved(p));
    setAttr('accent', p.accent, 'indigo');
    setAttr('scale', p.scale, 'default');
    setAttr('vision', p.vision, 'none');
    setAttr('contrast', p.contrast, 'normal');
    setAttr('density', p.density, 'comfortable');
    if (p.motion === 'reduce') root.setAttribute('data-motion', 'reduce'); else root.removeAttribute('data-motion');
    if (p.sidebar_collapsed) root.setAttribute('data-sidebar', 'collapsed'); else root.removeAttribute('data-sidebar');
    if (p.accent_custom) {
      root.style.setProperty('--primary', p.accent_custom);
      root.style.setProperty('--primary-600', p.accent_custom);
      root.style.setProperty('--primary-soft', `color-mix(in srgb, ${p.accent_custom} 14%, transparent)`);
      root.style.setProperty('--primary-ring', `color-mix(in srgb, ${p.accent_custom} 30%, transparent)`);
    } else {
      ['--primary', '--primary-600', '--primary-soft', '--primary-ring'].forEach(v => root.style.removeProperty(v));
    }
    document.querySelectorAll('[data-theme-icon]').forEach(el => { el.innerHTML = icon(resolved(p) === 'dark' ? 'sun' : 'moon'); });
  }

  // A change that repaints the whole page (theme, contrast, accent) is animated: a circle that grows from where the
  // person clicked when the browser can do it, a short cross-fade otherwise, nothing with reduced motion.
  function animated(change, ev) {
    if (reduced()) { change(); return; }
    if (document.startViewTransition) {
      const r = ev?.target?.getBoundingClientRect?.();
      root.style.setProperty('--vt-x', r ? `${r.left + r.width / 2}px` : '95%');
      root.style.setProperty('--vt-y', r ? `${r.top + r.height / 2}px` : '4%');
      document.startViewTransition(change);
    } else {
      root.classList.add('theme-fade');
      change();
      setTimeout(() => root.classList.remove('theme-fade'), 420);
    }
  }

  async function load() {
    try { cur = { ...DEFAULTS, ...(await apiRequest('/auth/preferences', { headers: { 'X-Impress-Background': '1' } })) }; } catch { /* keep the cached copy */ }
    apply(); cache();
    return cur;
  }

  async function save(patch, ev) {
    const visual = ['theme', 'accent', 'accent_custom', 'contrast', 'vision'].some(k => k in patch);
    const change = () => { cur = { ...cur, ...patch }; apply(); cache(); };
    if (visual) animated(change, ev); else change();
    if (!isLoggedIn()) return cur;
    try {
      const saved = await apiRequest('/auth/preferences', { method: 'PUT', body: JSON.stringify(patch) });
      cur = { ...cur, ...saved }; cache();
    } catch (err) { showToast(err.message, 'error'); }
    return cur;
  }

  function toggleTheme(ev) { return save({ theme: resolved() === 'dark' ? 'light' : 'dark' }, ev); }

  window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener?.('change', () => { if (cur.theme === 'system') { apply(); cache(); } });

  // ── dates, times, numbers ───────────────────────────────────────────
  const IST = 'Asia/Kolkata';
  function parts(epoch) {
    return Object.fromEntries(new Intl.DateTimeFormat('en-GB', { timeZone: IST, year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(epoch)).map(p => [p.type, p.value]));
  }
  function datePart(pt, withYear) {
    const { year: Y, month: m, day: d } = pt;
    switch (cur.date_format) {
      case 'mdy': return withYear ? `${m}/${d}/${Y}` : `${m}/${d}`;
      case 'ymd': return withYear ? `${Y}/${m}/${d}` : `${m}/${d}`;
      case 'iso': return withYear ? `${Y}-${m}-${d}` : `${m}-${d}`;
      case 'long': return `${+d} ${MONTHS[+m - 1]}${withYear ? ' ' + Y : ''}`;
      default: return withYear ? `${d}/${m}/${Y}` : `${d}/${m}`;
    }
  }
  function timePart(pt, seconds) {
    const sec = seconds ? `:${pt.second}` : '';
    if (cur.time_format === '12h') {
      const h = +pt.hour;
      return `${h % 12 || 12}:${pt.minute}${sec} ${h < 12 ? 'AM' : 'PM'}`;
    }
    return `${pt.hour}:${pt.minute}${sec}`;
  }
  /** What istFormat (app.js) calls: the person's date and time formats, for the options the page asked for. */
  function istFormat(epoch, o = {}) {
    const hasDate = !!(o.year || o.month || o.day), hasTime = !!(o.hour || o.minute || o.second);
    if (o.month === 'long' || o.weekday || (!hasDate && !hasTime)) return null;           // wording the formats don't change
    const pt = parts(epoch);
    const bits = [];
    if (hasDate) bits.push(datePart(pt, !!o.year || (!o.month && !o.day) || o.year));
    if (hasTime) bits.push(timePart(pt, cur.show_seconds));
    return bits.join(cur.date_format === 'iso' ? ' ' : ', ');
  }
  function number(n) { return n == null ? '—' : Number(n).toLocaleString(LOCALES[cur.number_format] || 'en-US'); }
  function weekdays() {
    const i = DAYS.indexOf(cur.week_start[0].toUpperCase() + cur.week_start.slice(1));
    return [...DAYS.slice(i), ...DAYS.slice(0, i)];
  }
  function sample() {
    const now = Date.now();
    return { date: istFormat(now, { year: 'numeric', month: 'short', day: 'numeric' }), time: istFormat(now, { hour: '2-digit', minute: '2-digit' }),
      number: number(1234567.5), both: istFormat(now, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) };
  }

  return { get cur() { return cur; }, DEFAULTS, ACCENTS, load, save, apply, resolved, reduced, toggleTheme, animated, istFormat, number, weekdays, sample,
    advanced: () => !!cur.advanced && typeof Shell !== 'undefined' && isAdminUser(Shell.user), cache };
})();

// Set the theme and the personal display settings before first paint to avoid a flash of the wrong look.
// A static file, not an inline script: the page's Content-Security-Policy forbids inline scripts.
// The saved preferences (prefs.js keeps this copy) are applied as attributes on <html>.
(function () {
  var root = document.documentElement;
  try {
    var p = JSON.parse(localStorage.getItem('impress_prefs') || '{}');
    var t = p.theme || localStorage.getItem('impress_theme');
    if (t !== 'light' && t !== 'dark') {
      t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    root.setAttribute('data-theme', t);
    ['accent', 'scale', 'vision', 'contrast', 'density'].forEach(function (k) {
      if (p[k] && p[k] !== 'default' && p[k] !== 'none' && p[k] !== 'normal' && p[k] !== 'comfortable') root.setAttribute('data-' + k, p[k]);
    });
    if (p.accent && p.accent !== 'indigo') root.setAttribute('data-accent', p.accent);
    if (p.motion === 'reduce') root.setAttribute('data-motion', 'reduce');
    if (p.sidebar_collapsed) root.setAttribute('data-sidebar', 'collapsed');
    if (p.accent_custom) {
      root.style.setProperty('--primary', p.accent_custom);
      root.style.setProperty('--primary-600', p.accent_custom);
    }
  } catch (e) {
    root.setAttribute('data-theme', 'light');
  }
})();

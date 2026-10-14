// Set the theme before first paint to avoid a flash of the wrong theme.
// A static file, not an inline script: the page's Content-Security-Policy forbids inline scripts.
(function () {
  try {
    var t = localStorage.getItem('impress_theme');
    if (t !== 'light' && t !== 'dark') {
      t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.setAttribute('data-theme', t);
  } catch (e) {
    document.documentElement.setAttribute('data-theme', 'light');
  }
})();

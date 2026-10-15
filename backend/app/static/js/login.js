/* imPress v2.2 sign-in page: one centred card, nothing else. Replaces the v2.1 renderLogin in app.js. */

async function renderLogin(app) {
  document.body.classList.remove('shell');
  if (!['disabled', 'restart'].includes(Overlays.shown)) {          // a notice about why you are here stays until you answer it
    document.body.classList.remove('blurred');
    document.getElementById('notice-overlay')?.remove();
  }
  Live.stop();
  await loadSystemStatus();
  const insecure = location.protocol === 'http:' && !['localhost', '127.0.0.1', '[::1]'].includes(location.hostname);
  const reason = getParams().get('reason');
  app.innerHTML = `
    <div class="login-page">
      <div class="login-shell">
        <section class="login-form-side">
          <button class="icon-btn login-theme" data-action="toggle-theme" aria-label="Switch between light and dark" data-theme-icon>${themeIcon()}</button>
          <form id="login-form" novalidate>
            <div class="login-brand login-card-in">${brandMark()}<span>imPress</span></div>
            <div class="login-card-in"><h1>Welcome back</h1><p class="lead">Sign in to your classroom account.</p></div>
            ${reason ? `<p class="callout info" role="status">${escHtml(reason)}</p>` : ''}
            <div class="form-group login-card-in">
              <label for="login-user">Username</label>
              <div class="input-icon">${icon('user')}<input type="text" id="login-user" required autocomplete="username" autocapitalize="none" spellcheck="false" placeholder="Your username" /></div>
            </div>
            <div class="form-group login-card-in">
              <label for="login-pass">Password</label>
              <div class="input-icon">${icon('lock')}<input type="password" id="login-pass" required autocomplete="current-password" placeholder="Your password" />
                <button type="button" class="btn btn-ghost btn-icon btn-sm trail" id="login-eye" aria-label="Show password">${icon('eye')}</button></div>
              <span id="login-caps" class="form-hint hidden">${icon('alert', 'sm')} Caps Lock is on</span>
            </div>
            ${insecure ? `<p class="callout danger" role="alert">This connection is not encrypted: your password would cross the network in plain text. Use the <strong>https://</strong> address of this server.</p>` : ''}
            ${System.test_mode_forced ? `<p class="callout info" role="status">${icon('flask', 'sm')} This server runs in test mode. Sign in as the default super admin, <b>impress.default.superAdmin</b>.</p>` : ''}
            <p id="login-error" class="callout danger hidden" role="alert"></p>
            <p id="login-wait" class="callout info hidden" role="status" aria-live="polite"></p>
            <button type="submit" class="btn btn-primary btn-block mt-1 login-card-in" id="login-go">${icon('login')} Sign in</button>
            <p class="text-muted text-sm text-center mt-2">Forgot your password? Ask an administrator to reset it.</p>
            <div class="login-foot">${icon('shield', 'sm')} <span>Sign-in is for faculty and administrators. Each account can be signed in on one device at a time.</span></div>
          </form>
        </section>
      </div>
    </div>`;
  const pass = document.getElementById('login-pass'), eye = document.getElementById('login-eye'), err = document.getElementById('login-error');
  const form = document.getElementById('login-form'), go = document.getElementById('login-go');
  const wait = document.getElementById('login-wait'), signIn = go.innerHTML;
  let inFlight = false, blockedUntil = 0, timer = null;
  try { blockedUntil = Number(sessionStorage.getItem('impress_login_retry_at')) || 0; } catch { /* storage unavailable */ }
  const tick = () => {
    if (!form.isConnected) { clearInterval(timer); timer = null; return; }
    const seconds = Math.max(0, Math.ceil((blockedUntil - Date.now()) / 1000));
    go.disabled = inFlight || seconds > 0;
    go.innerHTML = seconds ? `Try again in ${seconds} s` : inFlight ? 'Signing in…' : signIn;
    wait.classList.toggle('hidden', !seconds);
    if (seconds) wait.textContent = `Sign-in is paused after unsuccessful attempts. Try again in ${seconds} s. Your password is not checked during this wait.`;
    else {
      try { sessionStorage.removeItem('impress_login_retry_at'); } catch { /* storage unavailable */ }
      clearInterval(timer); timer = null;
    }
  };
  const startWait = (seconds) => {
    blockedUntil = Date.now() + seconds * 1000;
    try { sessionStorage.setItem('impress_login_retry_at', String(blockedUntil)); } catch { /* storage unavailable */ }
    if (!timer) timer = setInterval(tick, 250);
    tick();
  };
  if (blockedUntil > Date.now()) { timer = setInterval(tick, 250); tick(); }
  eye.onclick = () => {
    const show = pass.type === 'password';
    pass.type = show ? 'text' : 'password';
    eye.innerHTML = icon(show ? 'eyeOff' : 'eye');
    eye.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
  };
  pass.addEventListener('keyup', (e) => document.getElementById('login-caps').classList.toggle('hidden', !e.getModifierState?.('CapsLock')));
  const fail = (m) => { err.textContent = m; err.classList.remove('hidden'); };
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (inFlight || blockedUntil > Date.now()) return;
    err.classList.add('hidden');
    const username = document.getElementById('login-user').value.trim(), password = pass.value;
    if (!username || !password) return fail('Enter your username and password.');
    inFlight = true;
    tick();
    try {
      await authApi.login(username, password);
      const me = await authApi.me();
      Shell.user = me;
      await Prefs.load();
      if (me.must_change_password || (!me.onboarded && System.feature_flags?.onboarding !== false)) { Onboarding.run(me); return; }
      navigate(({ classrooms: isAdminUser(me) ? '#/admin/classes' : '#/classes', students: '#/admin/students' }[Prefs.cur.landing]) || '#/dashboard');
    } catch (ex) {
      if (ex.status === 429 && ex.retryAfter > 0) startWait(ex.retryAfter);
      else fail(ex.message || 'Could not reach the server. Check your connection and try again.');
    } finally {
      inFlight = false;
      if (form.isConnected) tick();
    }
  });
}

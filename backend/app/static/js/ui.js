/* imPress v2.2 UI layer: icons, the app shell (sidebar, top bar, banners),
 * toasts and notifications, live updates over Server-Sent Events, search.
 * Loaded after api.js and before app.js; pages call these helpers. */

// ── Icons (24×24 stroke icons, Lucide-style) ───────────────────────────
const ICONS = {
  layers: '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  school: '<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>',
  clipboard: '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  userCog: '<circle cx="10" cy="8" r="4"/><path d="M2 21a8 8 0 0 1 11-7.4"/><circle cx="18" cy="18" r="2.5"/><path d="M18 14v1.5M18 20.5V22M14 18h1.5M20.5 18H22"/>',
  userPlus: '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M19 8v6M16 11h6"/>',
  book: '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2Z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7Z"/>',
  radio: '<circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 19.07a10 10 0 0 1 0-14.14"/>',
  cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  flask: '<path d="M9 2h6"/><path d="M10 2v6L4.5 18.5A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.8-2.5L14 8V2"/><path d="M7 15h10"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  help: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
  login: '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  filter: '<path d="M22 3H2l8 9.5V19l4 2v-8.5L22 3Z"/>',
  chevronDown: '<path d="m6 9 6 6 6-6"/>', chevronRight: '<path d="m9 18 6-6-6-6"/>', chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>', check: '<path d="M20 6 9 17l-5-5"/>',
  checkCircle: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  xCircle: '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
  alert: '<path d="m10.3 3.9-8.4 14.5A2 2 0 0 0 3.6 21h16.8a2 2 0 0 0 1.7-2.6L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  wifi: '<path d="M5 12.6a10 10 0 0 1 14 0"/><path d="M8.5 16.1a5 5 0 0 1 7 0"/><path d="M2 8.8a15 15 0 0 1 20 0"/><path d="M12 20h.01"/>',
  wifiOff: '<path d="m2 2 20 20"/><path d="M8.5 16.4a5 5 0 0 1 7 0"/><path d="M5 12.9a10 10 0 0 1 5.2-2.8"/><path d="M12 20h.01"/>',
  refresh: '<path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/>',
  play: '<path d="m6 4 14 8-14 8Z"/>', stop: '<rect x="5" y="5" width="14" height="14" rx="2"/>', pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  trash: '<path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="m2 2 20 20"/><path d="M6.7 6.7C3.9 8.5 2 12 2 12s3.5 7 10 7c2 0 3.7-.6 5.2-1.6"/><path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-2.2 3.2"/>',
  lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
  shieldCheck: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
  crown: '<path d="m2 18 2-11 5 4 3-6 3 6 5-4 2 11Z"/><path d="M4 21h16"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  pin: '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  chart: '<path d="M3 3v18h18"/><path d="M8 17V10M13 17V6M18 17v-4"/>',
  zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z"/>',
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  server: '<rect x="2" y="3" width="20" height="8" rx="2"/><rect x="2" y="13" width="20" height="8" rx="2"/><path d="M6 7h.01M6 17h.01"/>',
  router: '<rect x="2" y="13" width="20" height="8" rx="2"/><path d="M6 17h.01M10 17h.01"/><path d="M15 13V7"/><path d="M12 7a3 3 0 0 1 6 0"/>',
  hub: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>',
  module: '<rect x="5" y="2" width="14" height="20" rx="3"/><path d="M9 6h6M9 18h6"/><circle cx="12" cy="12" r="2"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/>',
  fileCheck: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  more: '<circle cx="12" cy="5" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="12" cy="19" r="1.4"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  arrowLeft: '<path d="M19 12H5M12 19l-7-7 7-7"/>', arrowRight: '<path d="M5 12h14M12 5l7 7-7 7"/>',
  battery: '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 11v2"/><path d="M6 11v2"/>',
  code: '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
  poll: '<path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="5"/><rect x="12" y="8" width="3" height="9"/><rect x="17" y="5" width="3" height="12"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  power: '<path d="M18.4 6.6a9 9 0 1 1-12.8 0"/><path d="M12 2v10"/>',
  key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/>',
  sparkles: '<path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2Z"/><path d="M19 3v4M17 5h4"/>',
  table: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/>',
  save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10Z"/>',
  calculator: '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01M8 19h.01M12 19h.01M16 19h.01"/>',
  palette: '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.9 0 1.7-.7 1.7-1.6 0-.4-.2-.8-.5-1.1-.3-.3-.5-.7-.5-1.1 0-.9.7-1.7 1.7-1.7H16c3 0 6-2.2 6-6 0-4.9-4.5-8.5-10-8.5Z"/><path d="M6.5 12.5h.01M8.5 7.5h.01M13.5 6.5h.01M17.5 10.5h.01"/>',
  music: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
  heart: '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7Z"/>',
  leaf: '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z"/><path d="M2 21c0-3 1.9-5.5 6-7"/>',
  rocket: '<path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2.2 2.2 0 0 0-2.9-.1Z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.9A12.9 12.9 0 0 1 22 2c0 2.7-.8 7.5-6 11a22 22 0 0 1-4 2Z"/><path d="M9 12H4s.6-3 2-4c1.6-1.1 5 0 5 0"/><path d="M12 15v5s3-.6 4-2c1.1-1.6 0-5 0-5"/>',
  camera: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z"/><circle cx="12" cy="13" r="3"/>',
  panelLeft: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/>',
  keyboard: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M6 9h.01M10 9h.01M14 9h.01M18 9h.01M7 15h10"/>',
  compass: '<circle cx="12" cy="12" r="10"/><path d="m16.2 7.8-2.1 6.3-6.3 2.1 2.1-6.3Z"/>',
  sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
  type: '<path d="M4 7V4h16v3M9 20h6M12 4v16"/>',
  contrast: '<circle cx="12" cy="12" r="10"/><path d="M12 2v20"/><path d="M12 6a6 6 0 0 1 0 12"/>',
  accessibility: '<circle cx="12" cy="4.5" r="1.7"/><path d="M5 8.5c4.3 1.4 9.7 1.4 14 0M12 8.5V14m0 0-3 6.5M12 14l3 6.5"/>',
  trendUp: '<path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>',
  pie: '<path d="M21.2 15.9A10 10 0 1 1 8 2.8"/><path d="M22 12A10 10 0 0 0 12 2v10Z"/>',
  layout: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>',
  lifebuoy: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="m4.9 4.9 4.3 4.3M14.8 14.8l4.3 4.3M14.8 9.2l4.3-4.3M9.2 14.8l-4.3 4.3"/>',
  userCheck: '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="m16 11 2 2 4-4"/>',
  userX: '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="m17 8 5 5M22 8l-5 5"/>',
  undo: '<path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-15-6.7L3 13"/>',
  archive: '<rect x="2" y="3" width="20" height="5" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
  hardDrive: '<path d="M22 12H2"/><path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.7 4H7.3a2 2 0 0 0-1.8 1.1Z"/><path d="M6 16h.01M10 16h.01"/>',
  gauge: '<path d="m12 14 4-4"/><path d="M3.3 19a10 10 0 1 1 17.4 0"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9Z"/>',
  grip: '<circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>',
  maximize: '<path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/>',
  terminal: '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
  fingerprint: '<path d="M12 11c0 3.5-.5 6-1.5 8.5"/><path d="M8 14c0 2.6-.5 4.5-1 6"/><path d="M16 11.5c0 2.5-.3 5-1.2 7.5"/><path d="M5 10a7 7 0 0 1 14 0c0 1 0 2.4-.2 4"/><path d="M12 7a3 3 0 0 0-3 3"/>',
  bellRing: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/><path d="M2 8a10 10 0 0 1 3-6M22 8a10 10 0 0 0-3-6"/>',
  mapPin: '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.7 4H7.3a2 2 0 0 0-1.8 1.1Z"/>',
  unlock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>',
  swap: '<path d="m16 3 4 4-4 4"/><path d="M20 7H4"/><path d="m8 21-4-4 4-4"/><path d="M4 17h16"/>',
};

function icon(name, cls = '') {
  return `<svg class="ic ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ICONS.info}</svg>`;
}

// ── Passwords: the same rules as the server (passwords.py), for the strength meter ──
const COMMON_PASSWORDS = new Set(["0000000000", "0123456789", "1111111111", "1234567890", "12345678910", "1234abcd12", "1q2w3e4r5t", "abc1234567", "abcd123456", "abcdefghij", "admin12345", "admin@123", "admin@1234", "administrator", "asdfghjkl1", "changeme123", "changeme1234", "classroom1", "classroom123", "iloveyou12", "impress123", "impress1234", "letmein123", "p@ssw0rd", "p@ssword", "passw0rd", "passw0rd1", "password", "password1", "password12", "password123", "qwerty1234", "qwerty12345", "qwertyuiop", "rootroot12", "school1234", "student123", "student1234", "superadmin", "superadmin1", "teacher123", "teacher1234", "trustno1234", "welcome123", "welcome1234"]);

function passwordStrength(pw, username = '') {
  const checks = [['8 or more characters', pw.length >= 8], ['a lower-case letter', /[a-z]/.test(pw)], ['an upper-case letter', /[A-Z]/.test(pw)],
    ['a number', /[0-9]/.test(pw)], ['a special character', /[^A-Za-z0-9]/.test(pw)]];
  const missing = checks.filter(c => !c[1]).map(c => c[0]);
  const lowered = pw.toLowerCase();
  const bad = COMMON_PASSWORDS.has(lowered) || (username && lowered === username.trim().toLowerCase());
  const met = checks.length - missing.length;
  let score;
  if (!pw || bad) score = 0;
  else if (missing.length) score = met <= 2 ? 0 : 1;
  else score = 2 + (pw.length >= 12 ? 1 : 0) + (pw.length >= 16 ? 1 : 0);
  return { score, label: ['Too weak', 'Weak', 'Fair', 'Good', 'Strong'][score], missing, checks, common: !!bad };
}

/** Why a password is not acceptable for this role (null when it is): the server decides, this saves a round trip. */
function passwordProblem(pw, username = '', role = 'teacher') {
  const lowered = pw.toLowerCase();
  if (COMMON_PASSWORDS.has(lowered)) return 'is too common';
  if (username && lowered === username.trim().toLowerCase()) return 'must not be the username';
  if (role === 'super_admin') return pw.length < 10 ? 'must be at least 10 characters' : (new Set(pw).size < 4 ? 'uses too few different characters' : null);
  if (pw.length < 8) return 'must be at least 8 characters';
  if (!/[a-z]/.test(pw)) return 'needs a lower-case letter';
  if (!/[A-Z]/.test(pw)) return 'needs an upper-case letter';
  if (!/[0-9]/.test(pw)) return 'needs a number';
  if (!/[^A-Za-z0-9]/.test(pw)) return 'needs a special character (for example ! @ # $ %)';
  return null;
}

/** The meter under a password field: a bar that fills and recolours, the label, and the rules still to meet. */
function passwordMeterHtml(id) {
  return `<div class="pw-meter" id="${id}-meter" data-level="0" aria-hidden="true"><i></i></div>
    <div class="pw-hint"><span id="${id}-label" aria-live="polite"></span><span id="${id}-miss"></span></div>`;
}
function wirePasswordMeter(input, id, username = '', role = 'teacher') {
  const draw = () => {
    const pw = input.value, r = passwordStrength(pw, typeof username === 'function' ? username() : username);
    const meter = document.getElementById(`${id}-meter`);
    if (!meter) return;
    meter.dataset.level = pw ? String(Math.max(1, r.score)) : '0';
    meter.firstElementChild.style.width = pw ? `${Math.max(1, r.score) * 25}%` : '0';
    document.getElementById(`${id}-label`).textContent = pw ? (r.common ? 'Too common' : r.label) : '';
    document.getElementById(`${id}-miss`).textContent = pw && r.missing.length && role !== 'super_admin' ? `Needs ${r.missing.slice(0, 2).join(', ')}${r.missing.length > 2 ? '…' : ''}` : '';
  };
  input.addEventListener('input', draw);
  draw();
}

// ── Small components ──────────────────────────────────────────────────

function initials(name) {
  const parts = String(name || '?').replace(/^(Dr|Prof|Mr|Ms|Mrs)\.?\s+/i, '').trim().split(/\s+/);
  return ((parts[0] || '?')[0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase();
}

function avatar(name, size = '') {
  let h = 0;
  for (const ch of String(name || '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return `<span class="avatar ${size} c${(h % 6) + 1}" aria-hidden="true">${escHtml(initials(name))}</span>`;
}

function statCard(label, value, sub = '', iconName = 'grid', tone = '') {
  return `<div class="stat-card"><span class="stat-icon ${tone}">${icon(iconName)}</span>
    <div class="stat-label">${escHtml(label)}</div><div class="stat-value">${value}</div>
    ${sub ? `<div class="stat-sub">${sub}</div>` : ''}</div>`;
}

function statusPill(kind, text) {
  return `<span class="status ${kind}">${escHtml(text)}</span>`;
}

function emptyState(title, text = '', iconName = 'info') {
  return `<div class="empty">${icon(iconName)}<b>${escHtml(title)}</b>${text ? `<div>${text}</div>` : ''}</div>`;
}

function pageHeader(title, sub = '', actions = '', eyebrow = '') {
  return `<div class="page-header"><div>${eyebrow ? `<div class="eyebrow">${escHtml(eyebrow)}</div>` : ''}
    <h1>${escHtml(title)}</h1>${sub ? `<div class="page-sub">${sub}</div>` : ''}</div>
    ${actions ? `<div class="page-actions">${actions}</div>` : ''}</div>`;
}

function timeAgo(epoch) {
  if (!epoch) return '—';
  if (typeof Prefs !== 'undefined' && !Prefs.cur.relative_times) return istFormat(epoch, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  const s = Math.max(0, (Date.now() - epoch) / 1000);
  if (s < 45) return 'just now';
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  if (s < 86400 * 14) return `${Math.round(s / 86400)} d ago`;
  return istFormat(epoch, { day: 'numeric', month: 'short', year: 'numeric' });
}

function todayLabel() {
  return istFormat(Date.now(), { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).toUpperCase();
}

// ── Toasts and notifications ──────────────────────────────────────────

const _notices = [];

function showToast(message, type = 'info', { keep = false } = {}) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
  const ico = { success: 'checkCircle', error: 'xCircle', warning: 'alert' }[type] || 'info';
  toast.innerHTML = `${icon(ico)}<div></div><button aria-label="Dismiss">${icon('x', 'sm')}</button>`;
  toast.querySelector('div').textContent = message;
  const close = () => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 250); };
  toast.querySelector('button').onclick = close;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  if (!keep) setTimeout(close, type === 'error' ? 7000 : 3500);
}

// ── Notification tray ─────────────────────────────────────────────────
// Alerts from the server and from this page, newest first, grouped by day, with an unread count.
// Kept for the browser session (sessionStorage) so a page reload does not lose them.

const Tray = {
  items: [], tab: 'all',
  load() { try { this.items = JSON.parse(sessionStorage.getItem('impress_tray') || '[]'); } catch { this.items = []; } },
  save() { try { sessionStorage.setItem('impress_tray', JSON.stringify(this.items.slice(0, 60))); } catch { /* storage unavailable */ } },
  unread() { return this.items.filter(n => !n.read).length; },
  add(message, level = 'info', extra = {}) {
    this.items.unshift({ id: Date.now() + Math.random(), message, level, at: Date.now(), read: false, ...extra });
    this.items.length = Math.min(this.items.length, 60);
    this.save(); this.badge();
    if (document.getElementById('notice-pop') && !document.getElementById('notice-pop').classList.contains('hidden')) this.draw();
  },
  badge() {
    const el = document.getElementById('bell-count'), n = this.unread();
    if (!el) return;
    el.textContent = n > 9 ? '9+' : String(n);
    el.classList.toggle('hidden', n === 0);
  },
  day(at) {
    const d = new Date(at), t = new Date();
    if (d.toDateString() === t.toDateString()) return 'Today';
    if (d.toDateString() === new Date(t - 864e5).toDateString()) return 'Yesterday';
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  },
  draw() {
    const box = document.getElementById('notice-pop');
    if (!box) return;
    const list = this.items.filter(n => this.tab === 'all' || n.level === 'error' || n.level === 'warning');
    let last = '';
    const rows = list.map(n => {
      const d = this.day(n.at), head = d !== last ? `<div class="tray-day">${d}</div>` : '';
      last = d;
      const tone = n.level === 'error' ? 'red' : n.level === 'warning' ? 'amber' : n.level === 'success' ? 'green' : '';
      const ic = n.level === 'error' ? 'xCircle' : n.level === 'warning' ? 'alert' : n.level === 'success' ? 'checkCircle' : 'info';
      return `${head}<div class="tray-item ${n.read ? '' : 'unread'}" data-id="${n.id}"><span class="feed-icon ${tone}">${icon(ic, 'sm')}</span>
        <div style="flex:1;min-width:0"><p>${escHtml(n.message)}</p><time>${timeAgo(n.at)}</time></div>
        <button class="tray-x" data-action="tray-dismiss" data-id="${n.id}" aria-label="Dismiss">${icon('x', 'sm')}</button></div>`;
    }).join('');
    box.innerHTML = `<div class="tray-head"><b>Notifications</b>
        <button class="btn btn-ghost btn-sm" data-action="tray-read" ${this.unread() ? '' : 'disabled'}>${icon('check', 'sm')} Mark all read</button></div>
      <div class="tray-tabs" role="tablist">${[['all', 'All'], ['alerts', 'Alerts']].map(([k, t]) =>
        `<button role="tab" class="${this.tab === k ? 'active' : ''}" aria-selected="${this.tab === k}" data-action="tray-tab" data-tab="${k}">${t}</button>`).join('')}</div>
      <div class="tray-list">${rows || emptyState(this.tab === 'all' ? 'You are all caught up' : 'No alerts', 'New updates from imPress appear here.', 'bell')}</div>
      <div class="tray-foot"><span>${this.items.length} notification${this.items.length === 1 ? '' : 's'}</span>
        <button data-action="tray-clear" ${this.items.length ? '' : 'disabled'}>Clear all</button></div>`;
  },
};
Tray.load();

function addNotice(message, level = 'info', extra) { Tray.add(message, level, extra); }

window.toggleNotices = function (ev) {
  ev?.stopPropagation();
  const box = document.getElementById('notice-pop');
  if (!box) return;
  document.getElementById('help-menu')?.classList.add('hidden');
  document.getElementById('user-menu')?.classList.add('hidden');
  if (!box.classList.contains('hidden')) { box.classList.add('hidden'); return; }
  Tray.draw();
  box.classList.remove('hidden');
  setTimeout(() => { Tray.items.forEach(n => { n.read = true; }); Tray.save(); Tray.badge(); }, 1200);
};
document.addEventListener('click', (e) => {
  for (const [id, trigger] of [['notice-pop', '[data-action="toggle-notices"]'], ['help-menu', '[data-action="toggle-menu"]'], ['user-menu', '[data-action="toggle-menu"]']]) {
    const box = document.getElementById(id);
    if (box && !box.classList.contains('hidden') && !box.contains(e.target) && !e.target.closest(trigger)) box.classList.add('hidden');
  }
});

// ── Theme ─────────────────────────────────────────────────────────────

window.toggleTheme = function (ev) { Prefs.toggleTheme(ev); };


// ── System state: debug-mode banner, database status ──────────────────

const System = { testMode: false, db: 'ok', loaded: false };

async function loadSystemStatus() {
  try {
    const r = await fetch('/api/system/status', { headers: { 'X-Impress-Background': '1' } });
    if (r.ok) Object.assign(System, await r.json(), { loaded: true });
  } catch { /* offline: keep the last state */ }
  renderBanners();
}

// The banners above every page, stacked: the integrity-protection warning first (it cannot be dismissed), then test mode.
// The server decides which apply (GET /api/system/status: banners).
function renderBanners() {
  let el = document.getElementById('sys-banners');
  if (!el) {
    el = document.createElement('div');
    el.id = 'sys-banners';
    document.body.prepend(el);
  }
  const parts = [];
  const iips = (System.banners || []).find(b => b.id === 'iips');
  if (iips) {
    parts.push(`<div class="sys-banner integrity" role="alert" data-banner="iips">${icon('shield')}
      <span><b>Warning</b> &nbsp;${escHtml(iips.text)}</span>
      <button class="info-btn" data-info aria-label="What this means">${icon('info', 'sm')}<span class="tip" role="tooltip">The program's own files are no longer being checked against the reference made at first start. Root turned this off when starting the server. Restart without the bypass flag, or with the rehash flag, to restore it.</span></button></div>`);
  }
  if (System.test_mode) {           // live: the server's status events and the Test data page keep this current
    parts.push(`<div class="sys-banner test" role="status" data-banner="test">${icon('flask')}
      <span><b>Test mode</b> &nbsp;You are working on test data, not the real database.</span>
      <button class="info-btn" data-info aria-label="What this means">${icon('info', 'sm')}<span class="tip" role="tooltip">${System.test_mode_forced
        ? 'Root enabled test mode when the server was started. It cannot be turned off from the web app.'
        : 'Changes you make now do not affect the real classes. Turn test mode off, under Test data, to go back to the real data.'}</span></button></div>`);
  }
  if (System.db === 'degraded' && Shell.user && ['admin', 'super_admin'].includes(Shell.user.role)) {
    parts.push(`<div class="sys-banner degraded" role="alert">${icon('alert')}
      <span><b>Database restored.</b> It was changed outside imPress and has been repaired automatically. <a href="#/admin/system">Review</a></span></div>`);
  }
  el.innerHTML = parts.join('');
  document.body.classList.toggle('has-banner', parts.length > 0);
  document.documentElement.style.setProperty('--banner-h', `${el.offsetHeight}px`);
  const chip = document.getElementById('db-chip');
  if (chip) chip.classList.toggle('hidden', System.db !== 'degraded');
}

// ── Shell: sidebar + top bar ──────────────────────────────────────────

const Shell = { user: null, counts: {} };

const NAV = [
  { section: 'Workspace' },
  { href: '#/dashboard', label: 'Overview', icon: 'grid', match: ['#/dashboard', '#/admin'] },
  { href: 'classes', label: 'Classrooms', icon: 'school', match: ['#/classes', '#/admin/classes', '#/admin/classes/new', '#/class'], count: 'classes' },
  { href: '#/sessions', label: 'Quizzes & polls', icon: 'clipboard', match: ['#/sessions', '#/quiz', '#/poll', '#/quiz-results', '#/poll-results'] },
  { href: '#/admin/students', label: 'Students', icon: 'users', match: ['#/admin/students', '#/student'], perm: 'admin' },
  { href: '#/admin/courses', label: 'Courses', icon: 'book', match: ['#/admin/courses'], perm: 'admin' },
  { section: 'Administration', perm: 'admin' },
  { href: '#/admin/modules', label: 'Devices', icon: 'radio', match: ['#/admin/modules'], perm: 'admin' },
  { href: '#/admin/firmware', label: 'Firmware & OTA', icon: 'cpu', match: ['#/admin/firmware'], perm: 'admin' },
  { href: '#/admin/users', label: 'User access', icon: 'userCog', match: ['#/admin/users'], perm: 'admin' },
  { href: '#/admin/activity', label: 'Activity log', icon: 'history', match: ['#/admin/activity'], perm: 'admin' },
  { href: '#/admin/system', label: 'System', icon: 'database', match: ['#/admin/system'], perm: 'admin', dbChip: true },
  { href: '#/admin/test-data', label: 'Test data', icon: 'flask', match: ['#/admin/test-data'], perm: 'super' },
];

const CRUMBS = {
  '#/dashboard': ['Overview'], '#/admin': ['Overview'], '#/classes': ['Classrooms'], '#/admin/classes': ['Classrooms'],
  '#/admin/classes/new': ['Classrooms', 'Classroom'], '#/class': ['Classrooms', 'Classroom'],
  '#/sessions': ['Quizzes & polls'], '#/quiz': ['Quizzes & polls', 'Create quiz'], '#/poll': ['Quizzes & polls', 'Create poll'],
  '#/quiz-results': ['Quizzes & polls', 'Quiz results'], '#/poll-results': ['Quizzes & polls', 'Poll results'],
  '#/admin/students': ['Students'], '#/student': ['Students', 'Student'], '#/admin/courses': ['Courses'],
  '#/admin/modules': ['Administration', 'Devices'], '#/admin/firmware': ['Administration', 'Firmware & OTA'],
  '#/admin/users': ['Administration', 'User access'], '#/admin/activity': ['Administration', 'Activity log'],
  '#/admin/system': ['Administration', 'System'], '#/admin/test-data': ['Administration', 'Test data'],
  '#/settings': ['Settings'],
};

function isAdminUser(u) { return u && (u.role === 'admin' || u.role === 'super_admin'); }

function brandMark() { return `<span class="brand-mark">${icon('layers')}</span>`; }

function renderNavbar(user, currentHash) {
  Shell.user = user;
  const admin = isAdminUser(user);
  const superAdmin = user.role === 'super_admin';
  const items = NAV.filter(n => !n.perm || (n.perm === 'admin' && admin) || (n.perm === 'super' && superAdmin)).map(n => {
    if (n.section) return `<div class="nav-section">${escHtml(n.section)}</div>`;
    const href = n.href === 'classes' ? (admin ? '#/admin/classes' : '#/classes') : n.href;
    const active = n.match.includes(currentHash);
    const count = n.count && Shell.counts[n.count] ? `<span class="count">${String(Shell.counts[n.count]).padStart(2, '0')}</span>` : '';
    const chip = n.dbChip ? `<span id="db-chip" class="badge badge-danger badge-sm ${System.db === 'degraded' ? '' : 'hidden'}" style="margin-left:auto">Degraded</span>` : '';
    return `<a href="${href}" class="nav-item${active ? ' active' : ''}" data-tip="${escHtml(n.label)}"${active ? ' aria-current="page"' : ''}>${icon(n.icon)}<span>${escHtml(n.label)}</span>${count}${chip}</a>`;
  }).join('');
  const crumbs = ['Workspace', ...(CRUMBS[currentHash] || [])];
  const roleLabel = (typeof roleTitle === 'function') ? roleTitle(user) : ({ super_admin: 'Super admin', admin: 'Administrator', teacher: 'Faculty' }[user.role] || user.role);
  const name = user.name || user.display_name || user.full_name || user.username;
  document.body.classList.add('shell');          // #app sits beside the sidebar (CSS)
  setTimeout(afterShell, 0);
  return `
    <div class="app-scrim" data-action="nav-close"></div>
    <aside class="app-sidebar" aria-label="Main navigation" id="app-sidebar">
      <a href="#/dashboard" class="brand" aria-label="imPress home">${brandMark()}<span class="brand-name">imPress</span></a>
      <nav aria-label="Pages">${items}</nav>
      <div class="nav-foot">
        <button type="button" class="nav-item nav-collapse" data-action="sidebar-toggle" aria-controls="app-sidebar" data-tip="Expand sidebar">${icon('panelLeft')}<span>Collapse</span></button>
        <a href="#/settings" class="nav-item${currentHash === '#/settings' ? ' active' : ''}" data-tip="Settings">${icon('settings')}<span>Settings</span></a>
        ${admin && System.feature_flags?.help_menu !== false ? `<a href="#" class="nav-item" data-action="open-help" data-tip="Help &amp; documentation">${icon('lifebuoy')}<span>Help &amp; documentation</span></a>` : ''}
        <div class="user-card">${avatar(name, 'sm')}
          <div class="who"><b>${escHtml(name)}</b><span>${escHtml(roleLabel)}</span></div>
          <button class="btn btn-ghost btn-icon btn-sm" ${callAttr('handleLogout')} title="Sign out" aria-label="Sign out">${icon('logout')}</button>
        </div>
      </div>
    </aside>
    <div class="app-topbar-host">
      <header class="app-topbar">
        <button class="icon-btn menu-toggle" data-action="nav-toggle" aria-label="Menu">${icon('menu')}</button>
        <nav class="crumbs" aria-label="Breadcrumb">${crumbs.map((c, i) => i === crumbs.length - 1
          ? `<b>${escHtml(c)}</b>` : `<span>${escHtml(c)}</span><span class="sep">/</span>`).join('')}</nav>
        <div class="topbar-right">
          ${System.feature_flags?.search !== false ? `<button class="search-trigger" data-action="open-palette" aria-label="Search" aria-keyshortcuts="Control+K Meta+K">${icon('search', 'sm')}<span>Search or jump to…</span><kbd>${/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl'} K</kbd></button>` : ''}
          ${System.feature_flags?.tutorial !== false ? `<div class="menu-wrap"><button class="icon-btn" data-action="toggle-menu" data-menu="help-menu" aria-haspopup="menu" aria-label="Help and tutorial" title="Help">${icon('help')}</button>
            <div id="help-menu" class="menu hidden" role="menu">
              <button role="menuitem" data-action="start-tour">${icon('compass', 'sm')} Take the tour</button>
              <button role="menuitem" data-action="open-shortcuts">${icon('keyboard', 'sm')} Keyboard shortcuts</button>
              ${admin && System.feature_flags?.help_menu !== false ? `<button role="menuitem" data-action="open-help">${icon('lifebuoy', 'sm')} Help &amp; documentation</button>` : ''}
            </div></div>` : ''}
          ${System.feature_flags?.notifications !== false ? `<div class="menu-wrap">
            <button class="icon-btn" data-action="toggle-notices" aria-label="Notifications" aria-haspopup="dialog">${icon('bell')}<span id="bell-count" class="count-badge ${Tray.unread() ? '' : 'hidden'}">${Tray.unread() > 9 ? '9+' : Tray.unread()}</span></button>
            <div id="notice-pop" class="tray hidden" role="dialog" aria-label="Notifications"></div>
          </div>` : ''}
          <button class="icon-btn" data-action="toggle-theme" aria-label="Switch between light and dark" data-theme-icon>${themeIcon()}</button>
          <div class="menu-wrap"><button class="icon-btn" style="border:0;background:none;width:auto" data-action="toggle-menu" data-menu="user-menu" aria-haspopup="menu" aria-label="Your account">${avatar(name)}</button>
            <div id="user-menu" class="menu hidden" role="menu">
              <div class="menu-head"><b>${escHtml(name)}</b><span>@${escHtml(user.username)} · ${escHtml(roleLabel)}</span></div>
              <a role="menuitem" href="#/settings">${icon('settings', 'sm')} Settings</a>
              <button role="menuitem" data-action="start-tour">${icon('compass', 'sm')} Take the tour</button>
              <hr><button role="menuitem" class="danger" ${callAttr('handleLogout')}>${icon('logout', 'sm')} Sign out</button>
            </div></div>
        </div>
      </header>
    </div>`;
}

function themeIcon() {
  return icon(typeof Prefs !== 'undefined' && Prefs.resolved() === 'dark' ? 'sun' : 'moon');
}

function afterShell() {
  renderBanners();
  Live.start();
  Tray.badge();
  if (typeof Overlays !== 'undefined') Overlays.refresh();
  if (typeof Onboarding !== 'undefined') Onboarding.maybeAfterShell();
}

window.handleLogout = async function () {
  Live.stop();
  await authApi.logout();
  navigate('#/login');
};

// ── Live updates (Server-Sent Events) ─────────────────────────────────
/* The server says which tables changed; the page showing them refetches in
 * the background. A refresh never interrupts the user: it waits while a field
 * is focused or edited, a dialog is open, text is selected, or the user
 * interacted in the last few seconds, and retries shortly after. */

const ROUTE_TOPICS = {
  '#/dashboard': ['class_sessions', 'students', 'student_enrollments', 'esp_devices', 'student_modules', 'quizzes', 'polls', 'activity_logs', 'users'],
  '#/admin': ['class_sessions', 'students', 'esp_devices', 'student_modules', 'activity_logs', 'users'],
  '#/classes': ['class_sessions', 'student_enrollments', 'quizzes', 'polls', 'student_modules'],
  '#/admin/classes': ['class_sessions', 'student_enrollments', 'student_modules', 'class_faculty'],
  '#/sessions': ['quizzes', 'polls', 'quiz_answers', 'poll_votes'],
  '#/admin/students': ['students', 'student_enrollments', 'student_modules', 'attendance'],
  '#/admin/courses': ['courses'],
  '#/admin/modules': ['esp_devices', 'student_modules', 'deployment_targets'],
  '#/admin/firmware': ['firmware_artifacts', 'firmware_deployments', 'deployment_targets', 'esp_devices'],
  '#/admin/users': ['users', 'activity_logs', 'class_faculty'],
  '#/admin/activity': ['activity_logs'],
  '#/admin/system': ['activity_logs'],
  '#/quiz-results': ['quiz_answers'], '#/poll-results': ['poll_votes'],
  '#/student': ['students', 'quiz_answers', 'poll_votes', 'attendance', 'student_enrollments'],
};

const Live = {
  es: null, pending: null, lastUser: 0, timer: null, lastRun: 0,
  start() {
    if (this.es || !window.EventSource) return;
    this.es = new EventSource('/api/events');
    this.es.onmessage = (m) => {
      let ev;
      try { ev = JSON.parse(m.data); } catch { return; }
      if (ev.type === 'changed') this.changed(ev.topics || []);
      else if (ev.type === 'alert') { showToast(ev.message, ev.level === 'error' ? 'error' : ev.level, { keep: ev.level === 'error' }); addNotice(ev.message, ev.level); }
      else if (ev.type === 'update') { loadSystemStatus(); }
      else if (ev.type === 'status') {
        if ('test_mode' in ev) { System.test_mode = ev.test_mode; }
        if ('db' in ev) System.db = ev.db;
        renderBanners();
      } else if (ev.type === 'session_ended') {
        this.stop();
        Overlays.sessionEnded(ev.reason);
      }
    };
    this.es.onerror = () => {               // the browser reconnects by itself; stop if signed out
      if (!isLoggedIn()) this.stop();
    };
  },
  stop() { if (this.es) { this.es.close(); this.es = null; } },
  changed(topics) {
    const want = ROUTE_TOPICS[getRoute()];
    if (topics.some(t => ['firmware_deployments', 'deployment_targets'].includes(t))) loadSystemStatus();   // an update may have started or finished
    if (topics.includes('feature_flags')) loadSystemStatus();
    if (!want || !topics.some(t => want.includes(t))) return;
    this.pending = true;
    this.schedule(600);
  },
  schedule(ms) {
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.run(), ms);
  },
  busy() {
    if (Date.now() - this.lastUser < 4000) return true;
    if (document.querySelector('.modal:not(.hidden)')) return true;
    const a = document.activeElement;
    if (a && (a.matches('input, textarea, select, [contenteditable]'))) return true;
    if (String(window.getSelection?.() || '').length) return true;
    return [...document.querySelectorAll('#app input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=file]), #app textarea')]
      .some(el => el.value !== el.defaultValue && !el.dataset.live);
  },
  async run() {
    if (!this.pending) return;
    if (this.busy() || Date.now() - this.lastRun < 2000) { this.schedule(2500); return; }
    this.pending = false;
    this.lastRun = Date.now();
    await quietRefresh();
  },
};
['pointerdown', 'keydown', 'wheel'].forEach(t => window.addEventListener(t, () => { Live.lastUser = Date.now(); }, { passive: true }));
document.addEventListener('visibilitychange', () => { if (!document.hidden && Live.pending) Live.schedule(200); });


// ── Delegated events (v2.2) ──────────────────────────────────────────────
// The page has no inline handlers, so its Content-Security-Policy can forbid them
// (script-src 'self', no 'unsafe-inline'). Markup says what a click or key should do:
//
//   data-action="name"        Actions[name](element, event)        (also data-change, data-input, data-submit, data-keydown)
//   ${callAttr('fn', a, b)}   calls the named page function with JSON arguments; only names in CALLABLE
//
// A name is never looked up on window from the page's markup unless it is on the list below,
// and arguments are JSON, never code.
const Actions = {};
const CALLABLE = new Set([
  '_deactivateStudent', '_deleteCourse', '_editCourse', '_editStudent', '_hardDeleteStudent', '_pushOta',
  '_reactivateStudent', '_showDiagnostics', '_verifyModule', 'activateClass', 'addQuizQuestion', 'classSession',
  'deactivateClass', 'deleteClass', 'deleteUser', 'editUser', 'endPoll', 'endUserSessions', 'goNewSession', 'handleLogout',
  'newSession', 'nextQuestion', 'openManageFaculty', 'removeClassException', 'resetUserPassword', 'saveClassFaculty',
  'setUserActive', 'startPoll', 'startQuiz', 'stopQuiz', 'tdDeleteDataset', 'tdPending', 'toggleClassCsvImport',
  'toggleClassStudentForm', 'unenrollStudent', 'usersPage',
]);

function callAttr(name, ...args) {
  if (!CALLABLE.has(name)) console.error('callAttr: not on the CALLABLE list:', name);
  return `data-call="${escHtml(name)}" data-args="${escHtml(JSON.stringify(args))}"`;
}

(function wireDelegatedEvents() {
  const route = (type, attr) => document.addEventListener(type, (e) => {
    const el = e.target && e.target.closest ? e.target.closest(`[${attr}]`) : null;
    const fn = el && Actions[el.getAttribute(attr)];
    if (fn) fn(el, e);
  });
  [['click', 'data-action'], ['change', 'data-change'], ['input', 'data-input'], ['submit', 'data-submit'],
   ['keydown', 'data-keydown']].forEach(([t, a]) => route(t, a));
  document.addEventListener('click', (e) => {
    const el = e.target && e.target.closest ? e.target.closest('[data-call]') : null;
    if (!el || el.disabled) return;
    const name = el.getAttribute('data-call');
    const fn = CALLABLE.has(name) ? window[name] : null;
    if (typeof fn !== 'function') { console.error('data-call: no such function', name); return; }
    let args = [];
    try { args = JSON.parse(el.getAttribute('data-args') || '[]'); } catch { return; }
    fn(...args);
  });
})();

const _target = (el) => document.querySelector(el.dataset.target);
Object.assign(Actions, {
  'hide': (el) => _target(el)?.classList.add('hidden'),
  'show': (el) => _target(el)?.classList.remove('hidden'),
  'hide-parent': (el) => el.parentElement?.classList.add('hidden'),
  'hide-closest': (el) => el.closest(el.dataset.closest)?.classList.add('hidden'),
  'remove-closest': (el) => el.closest(el.dataset.closest)?.remove(),
  'nav-close': () => document.body.classList.remove('nav-open'),
  'nav-toggle': () => document.body.classList.toggle('nav-open'),
  'goto': (el) => { location.hash = el.dataset.href; },
  'back': (el, e) => { e.preventDefault(); history.back(); },
  'scroll-to': (el) => _target(el)?.scrollIntoView({ behavior: 'smooth' }),
  'toggle-theme': (el, e) => toggleTheme(e),
  'toggle-notices': (el, e) => toggleNotices(e),
  'slot-remove': (el) => { window.formScheduleSlots.splice(Number(el.dataset.i), 1); window.formRenderScheduleRows(); },
  'slot-field': (el) => { window.formScheduleSlots[Number(el.dataset.i)][el.dataset.field] = el.value; },
  'td-export': (el) => testModeApi.download('dataset', el.dataset.name).catch(e => showToast(e.message, 'error')),
});

// A small modal that asks for text (a password, a typed confirmation) and
// resolves with the values, or null when cancelled. Built with the DOM, no inline script.
function askDialog({ title, body = '', fields = [], confirm = 'Confirm', danger = false, validate = null }) {
  return new Promise((resolve) => {
    const m = document.createElement('div');
    m.className = 'modal';
    m.innerHTML = `<div class="modal-backdrop"></div>
      <form class="modal-content card" novalidate role="dialog" aria-modal="true" aria-label="${escHtml(title)}">
        <h2>${escHtml(title)}</h2>
        ${body ? `<div class="text-muted" style="margin-bottom:12px">${body}</div>` : ''}
        ${fields.map((f, i) => `<div class="form-group"><label for="dlg-${i}">${escHtml(f.label)}</label>
          <input id="dlg-${i}" name="${escHtml(f.name)}" type="${escHtml(f.type || 'text')}" autocomplete="${escHtml(f.autocomplete || 'off')}"
            placeholder="${escHtml(f.placeholder || '')}"></div>`).join('')}
        <div class="modal-actions"><button type="button" class="btn btn-outline" data-dlg="cancel">Cancel</button>
          <button type="submit" class="btn ${danger ? 'btn-danger' : 'btn-primary'}" ${validate ? 'disabled' : ''}>${escHtml(confirm)}</button></div>
      </form>`;
    document.body.appendChild(m);
    const form = m.querySelector('form');
    const done = (value) => { m.remove(); document.removeEventListener('keydown', onKey); resolve(value); };
    const values = () => Object.fromEntries(fields.map(f => [f.name, form.elements[f.name].value]));
    const refresh = () => { if (validate) form.querySelector('button[type=submit]').disabled = !validate(values()); };
    const onKey = (e) => { if (e.key === 'Escape') done(null); };
    document.addEventListener('keydown', onKey);
    m.querySelector('.modal-backdrop').addEventListener('click', () => done(null));
    m.querySelector('[data-dlg=cancel]').addEventListener('click', () => done(null));
    form.addEventListener('input', refresh);
    form.addEventListener('submit', (e) => { e.preventDefault(); if (!validate || validate(values())) done(values()); });
    const first = form.querySelector('input'); if (first) first.focus(); else form.querySelector('[type=submit]').focus();
  });
}

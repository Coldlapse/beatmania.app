/* ===========================================================================
 * theme.js — 테마(라이트/다크) 단일 컨트롤러
 *
 * 이전에는 같은 일을 네 군데서 서로 다르게 하고 있었다:
 *   common.html <head> 스크립트   -> 쿠키 읽어 <html data-theme>
 *   common.html </html> 뒤 스크립트 -> document.body.style 직접 조작
 *   common.js                     -> <body data-theme>  (CSS 는 html 을 보므로 무효였다)
 *   rankview.html 인라인           -> 자체 getCookie/setCookie + 자체 토글
 * 이제 이 파일 하나만 테마를 만진다.
 *
 * 저장은 쿠키가 아니라 localStorage 다. 테마는 서버가 알 필요가 없는 값이라
 * 매 요청 헤더에 실어 보낼 이유가 없다. (이 사이트는 이미 표시 설정을
 * localStorage 에 저장하고 있었다 — 다크모드만 혼자 쿠키였다.)
 *
 * 저장된 값이 없으면 OS 설정(prefers-color-scheme)을 따른다. 사용자가 한 번
 * 고르면 그 선택이 OS 설정을 이긴다.
 *
 * FOUC 방지: 이 파일의 apply() 는 common.html <head> 의 인라인 스크립트에서도
 * 같은 로직으로 한 번 실행된다. 그쪽이 먼저 돌아 첫 페인트 전에 속성이 붙는다.
 * =========================================================================== */
(function (window, document) {
  'use strict';

  var STORAGE_KEY = 'bm-theme';          // 'dark' | 'light' | (없음 = OS 따름)
  var LEGACY_COOKIE = 'darkmode';        // 예전 저장 방식. 1회 이관 후 폐기
  var ATTR = 'data-bs-theme';            // Bootstrap 5.3 과 같은 속성을 쓴다

  function systemPrefersDark() {
    return !!(window.matchMedia &&
              window.matchMedia('(prefers-color-scheme: dark)').matches);
  }

  function readStored() {
    try {
      var v = window.localStorage.getItem(STORAGE_KEY);
      if (v === 'dark' || v === 'light') { return v; }
    } catch (e) { /* 사생활 보호 모드 등에서 접근이 막힐 수 있다 */ }
    return null;
  }

  function store(theme) {
    try { window.localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}
  }

  /* 기존 사용자의 darkmode 쿠키를 localStorage 로 한 번 옮기고 쿠키는 지운다.
     이걸 안 하면 이미 다크모드를 쓰던 사람이 라이트로 되돌아가 버린다. */
  function migrateLegacyCookie() {
    if (readStored() !== null) { return; }
    var m = document.cookie.match(
      new RegExp('(?:^|; )' + LEGACY_COOKIE + '=([^;]*)'));
    if (!m) { return; }
    store(decodeURIComponent(m[1]) === 'true' ? 'dark' : 'light');
    document.cookie = LEGACY_COOKIE + '=; Max-Age=0; path=/';
  }

  function resolve() {
    var stored = readStored();
    if (stored) { return stored; }
    return systemPrefersDark() ? 'dark' : 'light';
  }

  function apply(theme) {
    document.documentElement.setAttribute(ATTR, theme);
    syncToggleButtons(theme);
    // 캔버스 재렌더처럼 CSS 로 안 되는 일은 이벤트를 듣는 쪽이 알아서 한다.
    // 여기서 dorender() 를 직접 부르지 마라 — 리스너와 이중 호출이 되고,
    // 렌더가 비동기라 서열표가 두 번 그려진다.
    document.dispatchEvent(
      new CustomEvent('bm:themechange', { detail: { theme: theme } }));
  }

  function syncToggleButtons(theme) {
    var dark = theme === 'dark';
    var buttons = document.querySelectorAll('[data-bm-theme-toggle]');
    for (var i = 0; i < buttons.length; i++) {
      var b = buttons[i];
      b.setAttribute('aria-pressed', dark ? 'true' : 'false');
      b.setAttribute('title', dark ? '라이트 모드로 전환' : '다크 모드로 전환');
      var icon = b.querySelector('i');
      if (icon) {
        icon.className = dark ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
      }
    }
  }

  var Theme = {
    current: function () {
      return document.documentElement.getAttribute(ATTR) || resolve();
    },
    set: function (theme) {
      store(theme);
      apply(theme);
    },
    toggle: function () {
      this.set(this.current() === 'dark' ? 'light' : 'dark');
    },
    /* 캔버스 스킨이 팔레트를 고를 때 쓴다 */
    isDark: function () { return this.current() === 'dark'; }
  };

  window.BMTheme = Theme;

  migrateLegacyCookie();
  apply(resolve());

  document.addEventListener('DOMContentLoaded', function () {
    syncToggleButtons(Theme.current());
    document.addEventListener('click', function (e) {
      var btn = e.target.closest && e.target.closest('[data-bm-theme-toggle]');
      if (btn) { e.preventDefault(); Theme.toggle(); }
    });
  });

  /* 사용자가 직접 고른 적이 없을 때만 OS 설정 변화를 따라간다 */
  if (window.matchMedia) {
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    var onChange = function (e) {
      if (readStored() === null) { apply(e.matches ? 'dark' : 'light'); }
    };
    if (mq.addEventListener) { mq.addEventListener('change', onChange); }
    else if (mq.addListener) { mq.addListener(onChange); }
  }
})(window, document);

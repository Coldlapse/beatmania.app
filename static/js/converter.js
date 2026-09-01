/*
 * 흰숫 변환기.
 *
 * 상태는 두 개뿐이다 — IIDX 기준 서든(0~1000)과 리프트(0~1000). 두 필드가
 * 그리는 화면은 언제나 같고, beatoraja 수치는 그때그때 계산해서 보여 준다.
 *
 * 게임이 실제로 하는 계산은 beatoraja -> IIDX 한 방향뿐이다.
 *     IIDX = floor(BMS * (1000 - LIFT) / 1000)
 * 그러므로 반대로 갈 때는 "이 식에 넣으면 S 가 나오는 가장 작은 BMS" 를
 * 찾아야 하고, 그것이 ceil 이다. 예전 구현은 floor 를 썼는데 리프트에 따라
 * 한 칸 모자란 값이 나왔다(LIFT=333, IIDX=100 -> 149 -> 다시 99).
 */
(function () {
  'use strict';

  var MAX = 1000;
  // 서든과 리프트를 합쳐 레인을 다 덮는 것은 게임에서도 가능한 설정이다.
  // 보기에 답답하다고 막으면 정답을 깎아 버린다(LIFT 400 / BMS 1000 의
  // 정답은 600 인데, 여유를 20 두면 580 이 나왔다).
  var DEFAULT_SUDDEN = 300;
  var DEFAULT_LIFT = 0;

  var state = { sudden: DEFAULT_SUDDEN, lift: DEFAULT_LIFT };
  var keepView = false;
  var fields = [];

  function clamp(v, lo, hi) {
    return v < lo ? lo : (v > hi ? hi : v);
  }

  function toBms(sudden, lift) {
    var room = MAX - lift;
    if (room <= 0) { return MAX; }
    return clamp(Math.ceil(sudden * MAX / room), 0, MAX);
  }

  function toIidx(bms, lift) {
    return clamp(Math.floor(bms * (MAX - lift) / MAX), 0, MAX);
  }

  /* 정수로 맞추고, 둘의 합이 레인(1000)을 넘지 않게 한다. */
  function normalise() {
    state.lift = clamp(Math.round(state.lift), 0, MAX);
    state.sudden = clamp(Math.round(state.sudden), 0, MAX - state.lift);
  }

  function setSudden(v) {
    if (isNaN(v)) { return; }
    state.sudden = v;
    normalise();
    render();
  }

  function setBmsSudden(v) {
    if (isNaN(v)) { return; }
    setSudden(toIidx(clamp(v, 0, MAX), state.lift));
  }

  function setLift(v) {
    if (isNaN(v)) { return; }
    var before = state.lift;
    state.lift = clamp(v, 0, MAX);
    if (keepView) {
      // 보이는 넓이 = 1000 - 서든 - 리프트. 리프트가 늘어난 만큼 서든을 줄이면
      // 그대로 유지된다.
      state.sudden = state.sudden - (state.lift - before);
    }
    normalise();
    render();
  }

  /* --- 그리기 ------------------------------------------------------ */

  function render() {
    var bms = toBms(state.sudden, state.lift);
    var suddenPct = state.sudden / MAX * 100;
    var liftPct = state.lift / MAX * 100;

    fields.forEach(function (f) {
      f.sudden.style.height = suddenPct + '%';
      f.lift.style.height = liftPct + '%';
      f.judge.style.bottom = liftPct + '%';

      var own = f.game === 'iidx' ? state.sudden : bms;
      writeInput(f.suddenInput, own);
      writeInput(f.liftInput, state.lift);

      // 덮개가 얇아지면 숫자가 들어갈 자리가 없다. 이때는 레인 쪽으로 뺀다.
      f.sudden.classList.toggle('is-thin', state.sudden < 90);
      f.lift.classList.toggle('is-thin', state.lift < 90);

      setSliderAria(f.suddenHandle, own);
      setSliderAria(f.liftHandle, state.lift);
    });

    echo('iidx-sudden', state.sudden);
    echo('bms-sudden', bms);
    echo('lift', state.lift);
  }

  function writeInput(el, v) {
    // 입력 중인 칸은 건드리지 않는다. 커서가 튀고 지우는 중에 값이 되돌아온다.
    if (document.activeElement === el) { return; }
    el.value = String(v);
  }

  function setSliderAria(el, v) {
    el.setAttribute('aria-valuenow', String(v));
  }

  function echo(name, v) {
    var nodes = document.querySelectorAll('[data-conv-echo="' + name + '"]');
    for (var i = 0; i < nodes.length; i++) {
      nodes[i].textContent = String(v);
    }
  }

  /* --- 끌기 -------------------------------------------------------- */

  function attachDrag(field, handle, kind) {
    var dragging = false;

    function valueAt(clientY) {
      var box = field.el.getBoundingClientRect();
      if (box.height <= 0) { return null; }
      var fromTop = (clientY - box.top) / box.height * MAX;
      // 서든은 위에서부터, 리프트는 아래에서부터 잰다.
      return kind === 'sudden' ? fromTop : MAX - fromTop;
    }

    handle.addEventListener('pointerdown', function (e) {
      dragging = true;
      handle.setPointerCapture(e.pointerId);
      handle.classList.add('is-dragging');
      e.preventDefault();
    });

    handle.addEventListener('pointermove', function (e) {
      if (!dragging) { return; }
      var v = valueAt(e.clientY);
      if (v === null) { return; }
      apply(kind, field, v);
    });

    function end(e) {
      if (!dragging) { return; }
      dragging = false;
      handle.classList.remove('is-dragging');
      if (handle.hasPointerCapture && handle.hasPointerCapture(e.pointerId)) {
        handle.releasePointerCapture(e.pointerId);
      }
    }
    handle.addEventListener('pointerup', end);
    handle.addEventListener('pointercancel', end);

    handle.addEventListener('keydown', function (e) {
      var step = e.shiftKey ? 10 : 1;
      var cur = kind === 'sudden'
        ? (field.game === 'iidx' ? state.sudden : toBms(state.sudden, state.lift))
        : state.lift;
      if (e.key === 'ArrowUp' || e.key === 'ArrowRight') {
        apply(kind, field, cur + step);
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') {
        apply(kind, field, cur - step);
      } else if (e.key === 'Home') {
        apply(kind, field, 0);
      } else if (e.key === 'End') {
        apply(kind, field, MAX);
      } else {
        return;
      }
      e.preventDefault();
    });
  }

  /* 어느 필드의 어느 모서리를 움직였느냐에 따라 해석이 다르다. */
  function apply(kind, field, raw) {
    var v = Math.round(raw);
    if (kind === 'lift') {
      setLift(v);
    } else if (field.game === 'iidx') {
      setSudden(v);
    } else {
      setBmsSudden(v);
    }
  }

  /* --- 시작 -------------------------------------------------------- */

  function init() {
    var els = document.querySelectorAll('[data-conv-field]');
    if (!els.length) { return; }

    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var f = {
        el: el,
        game: el.getAttribute('data-conv-field'),
        sudden: el.querySelector('[data-conv-cover="sudden"]'),
        lift: el.querySelector('[data-conv-cover="lift"]'),
        suddenHandle: el.querySelector('[data-conv-handle="sudden"]'),
        liftHandle: el.querySelector('[data-conv-handle="lift"]'),
        judge: el.querySelector('.bm-judgeline')
      };
      f.suddenInput = f.sudden.querySelector('input');
      f.liftInput = f.lift.querySelector('input');

      attachDrag(f, f.suddenHandle, 'sudden');
      attachDrag(f, f.liftHandle, 'lift');

      bindInput(f, f.suddenInput, 'sudden');
      bindInput(f, f.liftInput, 'lift');

      fields.push(f);
    }

    var keep = document.querySelector('[data-conv-keepview]');
    if (keep) {
      keep.addEventListener('change', function () { keepView = keep.checked; });
    }
    var reset = document.querySelector('[data-conv-reset]');
    if (reset) {
      reset.addEventListener('click', function () {
        state.sudden = DEFAULT_SUDDEN;
        state.lift = DEFAULT_LIFT;
        render();
      });
    }

    render();
  }

  function bindInput(field, input, kind) {
    input.addEventListener('input', function () {
      // 비어 있는 동안에는 0 으로 되돌리지 않는다. 지우고 다시 치는 중이다.
      if (input.value === '') { return; }
      apply(kind, field, parseInt(input.value, 10));
    });
    input.addEventListener('blur', function () { render(); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

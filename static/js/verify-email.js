/* 이메일 인증 위젯.
 *
 * templates/user/_verify_email.html 과 짝이다. 서버와는 JSON 으로만 말한다.
 *
 * 여기서 하지 않는 것: 인증 상태를 기억하지 않는다. 서버 세션이 진실이고,
 * 폼을 제출하면 서버가 다시 확인한다. 이 스크립트를 건너뛰어 폼을 바로
 * 보내도 가입은 되지 않는다.
 */
(function () {
  'use strict';

  function csrf() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
      body: JSON.stringify(body)
    }).then(function (r) { return r.json(); });
  }

  document.querySelectorAll('.bm-verify').forEach(function (box) {
    var purpose = box.dataset.purpose;
    var field = document.querySelector('[name="' + box.dataset.field + '"]');
    var sendBtn = box.querySelector('.bm-verify-send');
    var codeRow = box.querySelector('.bm-verify-code-row');
    var codeInput = box.querySelector('.bm-verify-code');
    var checkBtn = box.querySelector('.bm-verify-check');
    var msg = box.querySelector('.bm-verify-msg');
    var timer = box.querySelector('.bm-verify-timer');
    var tick = null;

    function say(text, kind) {
      msg.textContent = text || '';
      msg.className = 'bm-verify-msg small mt-2 ' +
        (kind === 'ok' ? 'text-success' : kind === 'err' ? 'text-danger'
                                                         : 'text-body-secondary');
    }

    // 재발송까지 남은 시간을 보여 준다. 버튼만 잠가 두면 얼마나 기다려야
    // 하는지 알 수 없어 계속 누르게 된다.
    function countdown(sec) {
      clearInterval(tick);
      sendBtn.disabled = true;
      function paint() {
        if (sec <= 0) {
          clearInterval(tick);
          timer.textContent = '';
          sendBtn.disabled = false;
          return;
        }
        var m = Math.floor(sec / 60), s = sec % 60;
        timer.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        sec -= 1;
      }
      paint();
      tick = setInterval(paint, 1000);
    }

    sendBtn.addEventListener('click', function () {
      if (!field || !field.value.trim()) {
        say(sendBtn.dataset.needEmail || '이메일을 먼저 입력해 주세요.', 'err');
        if (field) { field.focus(); }
        return;
      }
      sendBtn.disabled = true;
      say('');
      post('/account/verify/send/', {email: field.value, purpose: purpose})
        .then(function (d) {
          say(d.message, d.ok ? 'ok' : 'err');
          if (d.ok) {
            codeRow.classList.remove('d-none');
            codeInput.focus();
            countdown(300);            // 서버의 재발송 간격과 같은 5분
          } else {
            sendBtn.disabled = false;
          }
        })
        .catch(function () {
          say('요청을 보내지 못했습니다. 잠시 뒤 다시 시도해 주세요.', 'err');
          sendBtn.disabled = false;
        });
    });

    checkBtn.addEventListener('click', function () {
      checkBtn.disabled = true;
      post('/account/verify/check/',
           {email: field.value, purpose: purpose, code: codeInput.value})
        .then(function (d) {
          say(d.message, d.ok ? 'ok' : 'err');
          checkBtn.disabled = false;
          if (d.ok) {
            // 인증이 끝나면 주소를 잠근다. 여기서 주소를 바꾸면 서버가
            // 제출을 거부하는데, 그 사실을 제출 후에 알면 헛수고다.
            if (field) { field.readOnly = true; }
            codeRow.classList.add('d-none');
            sendBtn.classList.add('d-none');
            timer.textContent = '';
            clearInterval(tick);
          }
        })
        .catch(function () {
          say('요청을 보내지 못했습니다.', 'err');
          checkBtn.disabled = false;
        });
    });

    codeInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); checkBtn.click(); }
    });
  });
})();

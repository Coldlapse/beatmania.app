// static/js/common.js
//
// 다크 모드 관련 코드는 static/js/theme.js 로 옮겼다.
// 여기에 다시 넣지 마라 — 예전에 같은 로직이 네 군데 흩어져 서로 충돌했고,
// 그중 이 파일의 것은 <body> 에 속성을 걸어서 아예 동작하지 않았다
// (CSS 는 html[data-theme] 를 본다).
//
// 드롭다운 수동 제어(BS3 시절의 우회)도 제거했다. Bootstrap 5 번들이 처리한다.


// 곡 랭킹·유저 랭킹·곡 목록(2026-09-26 삭제)만 쓰던 JSON 적재·DataTables 정렬·로딩 화면,
// 부르는 곳이 없던 저장 문자열·등급 변환 함수는 지웠다.

/* uses local storage for save/load settings */
function loadSetting(key, def) {
	if (typeof(Storage) !== "undefined") {
		r = localStorage.getItem(key);
		if (r == undefined) {
			return def;
		} else {
			return r;
		}
	} else {
		/* this browser doesn't support Local Storage Objects, sorry! */
		return def;
	}
}
function saveSetting(key, val) {
	if (typeof(Storage) !== "undefined") {
		localStorage.setItem(key, val);
		return val;
	} else {
		/* this browser doesn't support Local Storage Objects, sorry! */
		return undefined;
	}
}

function registerRecentuser(username) {
  var users = getRecentusers();
  var idx = users.indexOf(username);
  if (idx >= 0) {
    console.log(users);
    users.splice(idx, 1);
    console.log(users);
  }
  if (users.length > 5)
    users.pop();
  users.unshift(username);
  console.log(users);
  saveSetting("recentuser", JSON.stringify(users));
}

function getRecentusers() {
  var json = loadSetting("recentuser");
  var users = []
  if (json) {
    users = JSON.parse(json);
  }
  return users;
}

function showMessage(message) {
	// temporarily message, so it'll fade out automatically.
	$("#message").text(message);
	$("#message").show();
	if (typeof _tid !== 'undefined') {
		clearTimeout(_tid);
	}
	_tid = setTimeout(function() {
		$("#message").fadeOut(2000);
	}, 5000);
}



/*
 * for user page
 */
$(function() {
  function moveUserpage(username) {
    window.location.href = '/' + username;
    // register to recent user
    registerRecentuser(username);
  }
  $('#goto').click(function (e) {
    moveUserpage($('#searchuser').val());
  });
  $('#searchuser').keypress(function (e) {
    if (e.which == 13) {
      moveUserpage($('#searchuser').val());
    }
  });
});

/*
 * download canvas
 */
// 브라우저 안에서 PNG 로 만들어 바로 내려받는다. 전에는 PNG(약 900KB, base64 1.2MB)를
// 서버(/imgdownload/)에 올렸다가 되돌려받았다 — 그 입구가 인증·CSRF 없이 받은 바이트를
// 받은 파일명 그대로 내려줘서, 남의 페이지가 beatmania.app 출처로 임의 파일을 내려받게 할 수
// 있었다. 2026-09-26 에 지웠다.
function downloadCanvas(c, fn) {
  fn = fn !== undefined ? fn : "download.png";
  c.toBlob(function (blob) {
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = fn;
    document.body.appendChild(link);
    link.click();
    link.remove();
    // 내려받기가 시작된 뒤에 놓아 준다(바로 놓으면 일부 브라우저가 받지 못한다)
    setTimeout(function () { URL.revokeObjectURL(url); }, 10000);
  }, 'image/png');
}
$(function() {
  $("#capture").click(function () {
    downloadCanvas($("#rankimg canvas")[0]);
  });
});

/*
 * theme
 */
$(function() {
  $(".list.theme li").each(function (i,obj) {
    $(obj).click(function() {
      $(".list.theme li").removeClass("sel");
      $(this).addClass("sel");
      // re-render table
      dorender($(this).attr("data-value"));
    });
  });
});






/*
 * edit tool
 */
function _submit(action,v) {
  $('#editform-action').val(action);
  $('#editform-v').val(v);
  var jstr = $('#editform').serialize();
  console.log(jstr);
  $.ajax({
    url: "/modify/",
    type: "POST",
    data: jstr,
    success: function(r) {
      console.log(r);
      showMessage(r.message);
    }
  });
}
$(function() {
  var submit = _submit;

  $('#editstart').on('click touch', function () {
    var clears = ['0','1','2','3','4','5','6','7'];
    var ranks = ['F','E','D','C','B','A','AA','AAA','MAX'];
    $('#editwidget').removeClass('beforeedit');
    $('#editwidget').addClass('afteredit');
    /* load ranktable from webpage */
    $('#editsonglist').load('./table/?edit=1', function () {
      /* attach edit button to each songs */
      $('.edit-rank').on('click touch', function(e) {
        var rank_str = $(this).attr('data-rank');
        var rank = ranks.indexOf(rank_str);
        if (rank < 0) {
          alert('error');
          return;
        }
        $(this).removeClass('edit-rank-'+ranks[rank]);
        rank = (rank+1)%(ranks.length);
        $(this).addClass('edit-rank-'+ranks[rank]);
        $(this).attr('data-rank', ranks[rank]);
        var param = [{'id':parseInt($(this).parent().attr('data-id')),'rank':rank}];
        submit('edit',JSON.stringify(param));
        return false;
      });
      $('.edit-clear').on('click touch', function(e) {
        var clear = parseInt($(this).attr('data-clear'));
        $(this).removeClass('edit-clear-'+clears[clear]);
        clear = (clear+1)%(clears.length);
        $(this).addClass('edit-clear-'+clears[clear]);
        $(this).attr('data-clear', clear);
        var param = [{'id':parseInt($(this).parent().attr('data-id')),'clear':clear}]
        submit('edit',JSON.stringify(param));
        return false;
      });
    });
    return false;
  });

  /* If web cache exists, then ask and remove it */
  if (typeof tablename !== "undefined" &&
      typeof editmode !== "undefined" && 
      editmode) {
    var tname =tablename;
    var key = tname+"_data";
    var savedata = loadSetting(key);
    if (savedata) {
      var chk = confirm("기존에 저장된 데이터를 발견했습니다.\n취소시 기존 데이터를 삭제합니다.\n불러오시겠습니까? [y/n]");
      if (chk == false) {
        localStorage.removeItem(key);
        alert('삭제 완료');
      } else if (chk == true) {
        var savedata = JSON.parse(savedata);
        if (savedata.savedata_version != 1.0) {
          console.log(savedata.savedata_version);
          alert("버전이 호환되지 않아 불러올 수 없습니다.");
          return;
        }
        var param = [];
        for (var pkid in savedata.songs) {
          var sitem = savedata.songs[pkid];
          var item = {
            'id': pkid,
            'clear': sitem.clear,
            'rate': sitem.rate
          };
          param.push(item);
        }
        console.log(param);
        submit('edit',JSON.stringify(param));
        alert("불러오기 완료");
      }
    }
  }
});

/* 캔버스 배경색을 theme.css 의 --bm-canvas-bg 에서 읽는다.
   캔버스는 다운로드되어 공유되는 결과물이라 색을 바꾸지 않는다(라이트 #FFF,
   다크 #1F1F23). 대신 서열표 페이지의 배경이 같은 토큰을 쓰도록 해서
   캔버스가 페이지 위에 다른 판때기처럼 떠 보이지 않게 한다.
   두 값이 한 곳에서 나오므로 어긋날 수 없다. */
function bmCanvasBackground(fallback) {
  try {
    var v = getComputedStyle(document.documentElement)
              .getPropertyValue('--bm-canvas-bg').trim();
    if (v) { return v; }
  } catch (e) {}
  return fallback;
}

//
// very-default skin of table renderer of @lazykuna
// by @lazykuna MIT License
//

function Default2Renderer(ctx) {
  var self = this;
  self.ctx = ctx;
  // load image/resources
  var img_loadcnt = 0;
  var img_clear = new Image();
  var img_score = new Image();
  img_clear.onload = function() { img_loadcnt++; }
  img_score.onload = function() { img_loadcnt++; }
  self.isLoaded = function() { return img_loadcnt >= 2; }
  img_clear.src = "/static/img/clearlamp2.png";
  img_score.src = "/static/img/rank2.png";

  //
  // privates
  //
  var drawBLine = function(x1,y1,x2,y2,clr) {
    self.ctx.strokeStyle = clr!==undefined ? clr : "#000";
    self.ctx.lineWidth=1.5;
    self.ctx.moveTo(x1-0.5, y1-0.5);
    self.ctx.lineTo(x2-0.5, y2-0.5);
    self.ctx.stroke();
  };

  var drawCLine = function(x1,y1,x2,y2,clr) {
    self.ctx.strokeStyle = clr!==undefined ? clr : "#666";
    self.ctx.lineWidth=1;
    self.ctx.moveTo(x1-0.5, y1-0.5);
    self.ctx.lineTo(x2-0.5, y2-0.5);
    self.ctx.stroke();
  };

  //
  // common works
  //

  /** Theme Constants */
  self.width = 1200;
  self.colwidth = 140;
  self.itemcol = 6;
  self.itemheight = 30;
  self.margin_top = 150;
  self.margin_bottom = 100;
  self.theme_cate_margin = 0;
  self.theme_maincate_margin = 30;
  self.drawscore = true;
  self.dark = false;
  self.renderforprint = false;
  self.drawCell = function(d,x,y,w,h) {
      /*
       * INFO table function will automatically close path
       * So you don't have to do beginpath ~ closepath.
       */

      // 1 draw background
      self.ctx.fillStyle="#FFFFFF";
      if (d.data.diff == 'H') {
        self.ctx.fillStyle="#FFFFF0";
      } else if (d.data.diff == 'N') {
        self.ctx.fillStyle="#F0F0FF";
      } else if (d.data.diff == 'L') {
        self.ctx.fillStyle="#FFF0FF";
      }
      if (d.data.lvhd == 1) {
        self.ctx.fillStyle="#1F1F23";
      }
      self.ctx.fillRect(x,y,w,h);
      // 2 draw font
      fnt_color = "#000";
      if (d.data.lvhd == 1) {
        fnt_color = "#FFF";
      }
      curr_version = window._cur_version;
      if (!curr_version) curr_version = 99;
      if (d.data.version >= curr_version) fnt_color = "#C6F";
      tdrawer = new TextDrawer(self.ctx, "12px Arial", "9px Arial", fnt_color);
      tdrawer.drawText(d.data.title,x,y+h/2+4,w-35,h);
      // 3 draw border
      drawCLine(x,y,x+w,y);
      drawCLine(x,y+h,x+w,y+h);
      drawCLine(x+w,y,x+w,y+h);
      // 4 draw lamp
      if (d.clear > 0) {
        self.ctx.drawImage(img_clear,
            0,30 * (d.clear-1),15,30,
            x+w-15,y,15,h);
      }
      self.rank_count[d.clear]++;   // accumulate count
      // 4 score TODO
      if (self.drawscore) {
        var sx = 0;
        var sy = -1;
        var sw = 16;
        var sh = 16;
        /*
        if (d.rank == "F") sy = 116;
        else if (d.rank == "E") sy = 100;
        else if (d.rank == "D") sy = 83;
        else if (d.rank == "C") sy = 67;
        else */if (d.rank == "4") sy = 50;
        else if (d.rank == "5") sy = 33;
        else if (d.rank == "6") sy = 16;
        else if (d.rank == "7") sy = 0;
        else if (d.rank == "8"){
          sy = 132;
          sw = 21;
        }
        if (sy >= 0)
        {
          self.ctx.drawImage(img_score,
              sx,sy,sw,sh,
              x+w-40,y+9,sw,sh);
        }
      }
  }

  self.drawCategory = function(d,x,y,w,h,idx) {
    self.ctx.fillStyle="#EEE";
    self.ctx.fillRect(x,y,w,h);

    self.ctx.font = "bold 13px Arial";
    self.ctx.textAlign="center";
    self.ctx.fillStyle="#000000";
    self.ctx.fillText(d.category, x+w/2, y+h/2+4);

    // lamp
    var totalcnt = d.items.length;
    var clear = d.categoryclear;
    if (clear < 10 && clear > 0) {
      self.ctx.drawImage(img_clear,
          0,30 * (clear-1),15,30,
          x+w-15,y-1,14,h+1);
    }

    // border
    self.ctx.beginPath();
    drawCLine(x+w,y,x+w,y+h,"#333");
    drawCLine(x,y,x,y+h,"#333");
    // sadangborder
    drawCLine(x,y,x+w,y, "#333")
    self.ctx.closePath();
    if (d.categorytype == 1 && idx > 0)
    {
      self.ctx.beginPath();
      drawCLine(x,y,x+w,y);
      drawCLine(x,y-30,x+w,y-30);
      self.ctx.closePath();
    }
  }

  self.drawCategoryBox = function(d,x,y,w,h,idx) {
    self.ctx.beginPath();
    if (d.categorytype == 1 && idx > 0) {
      //drawBLine(x, y-30, x+w, y-30);
      //drawBLine(x, y-15, x+w, y-15);
    }
    self.ctx.closePath();
  }

  self.drawTableBefore = function(d,x,y,w,h) {
    var userdata = d.userdata;
    var tableinfo = d.tableinfo;

    var title = d.tableinfo.title;
    if (!title) title = d.title;
    var username = d.userdata.djname;
    if (!username) username = d.username;
    var spclass = d.userdata.spclass;
    var dpclass = d.userdata.dpclass;
    var spclassstr = d.userdata.spclassstr;
    var dpclassstr = d.userdata.dpclassstr;

    // init
    self.rank_count = [0,0,0,0,0,0,0,0];

    // 사이트 배경과 같은 색으로 채운다
    self.ctx.fillStyle = bmCanvasBackground("#ffffff");
    self.ctx.fillRect(0, 0, self.ctx.canvas.width, self.ctx.canvas.height);

    // render tablename (as background)
    if (d.tableinfo.tablename)
    {
      self.ctx.fillStyle="#F0F0F0";
      self.ctx.font = "bold italic 120px Arial";
      self.ctx.fillText(d.tableinfo.tablename, x+w-350, 120);
    }

    // render title
    self.ctx.font = "bold 30px Arial";
    self.ctx.textAlign="center";
    self.ctx.strokeStyle="#333";
    self.ctx.shadowColor="#000000";
    self.ctx.shadowBlur=5;
    self.ctx.miterLimit=1;
    self.ctx.lineWidth=5;
    self.ctx.strokeText(title, x+w/2, 70);
    self.ctx.shadowBlur=0;
    self.ctx.fillStyle="#EEE";
    self.ctx.fillText(title, x+w/2, 70);

    // DJ name, clear status
    self.ctx.fillStyle="#000";
    roundRect(self.ctx, x+10, 115, 100, 25, 5, true, false);
    self.ctx.font = "bold 14px Arial";
    self.ctx.textAlign="left";
    self.ctx.fillStyle="#FFF";
    self.ctx.fillText("DJ " + username, x + 20, 132);
    self.ctx.font = "bold 14px Arial";
    self.ctx.fillStyle="#000";
    self.ctx.fillText(d.userdata.iidxid, x + 120, 132);

    var gradecolor = [
      "#000000",
      "#000000",
      "#AADD33",  // 2
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#3399FF",  // 9
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#FF6666",  // 17
      "#FF6666",
      "#999999",  // 19
      "#DDDD33",  // 20
      ]
    if (spclass > 0) {
      self.ctx.fillStyle=gradecolor[spclass];
      roundRect(self.ctx, x+w-125, 115, 60, 25, {tl:5,tr:0,br:0,bl:5}, true, false);
      self.ctx.fillStyle=gradecolor[dpclass];
      roundRect(self.ctx, x+w-65, 115, 60, 25, {tl:0,tr:5,br:5,bl:0}, true, false);
      self.ctx.fillStyle="#FFF";
      self.ctx.font = "bold 14px Arial";
      self.ctx.fillText("SP" + spclassstr, x+w-120, 132);
      //self.ctx.fillText("/", x+w-68, 132);
      self.ctx.fillText("DP" + dpclassstr, x+w-60, 132);
    }

    // draw top line
    self.ctx.beginPath();
    drawBLine(x, 150, x+w, 150);
    self.ctx.closePath();
  }

  function formatDate(d) {
    var month = '' + (d.getMonth()+1);
    var day = '' + d.getDate();
    var year = d.getFullYear();
    if (month.length < 2) month = '0'+month;
    if (day.length < 2) day = '0'+day;
    return [year, month, day].join('-');
  }

  self.drawTableAfter = function(d,x,y,w,h) {
    var tabletime = d.tableinfo.time;
    var copyright = d.tableinfo.copyright;

    // very bottom line
    self.ctx.beginPath();
    drawCLine(x, y+h, x+300, y+h);
    self.ctx.closePath();
    y += 20;
    // date
    self.ctx.fillStyle="#999";
    self.ctx.font = "13px Arial";
    self.ctx.textAlign="right";
    var tdate = new Date(tabletime * 1000);
    self.ctx.fillText("Today: " + formatDate(new Date()) + " / Updated: " + formatDate(tdate),
        x+w, y+h+20);
    // copyright
    if (copyright) {
      self.ctx.textAlign="left";
      self.ctx.fillText(copyright, x, y+h+20);
    }


    var rate_fillstyle = ["#fff", "#eee", "#c99", "#9c6"/*E*/, "#9ac", "#e33", "#ec0", "#6ee"];
    var ey = y+h;

    // rank count
    var rank_box_wid = 35;
    var rank_box_hei = 15;
    var rank_box_yoff = 36;
    var rank_box_xoff = 150;
    var rank_box_wid_tot = 480;

    var rbox_xwidoff = (rank_box_wid_tot - rank_box_wid)/(8-1);
    var rbox_xoff = rank_box_xoff + x;
    for (var i=0; i<8; i++)
    {
      if (self.rank_count[i] > 0)
      {
        self.ctx.fillStyle = rate_fillstyle[i];
        self.ctx.strokeStyle = "#333";
        var is_stroke = false;
        if (i == 0) is_stroke = true;
        roundRect(self.ctx, rbox_xoff, ey+rank_box_yoff, rank_box_wid, rank_box_hei, 5, true, is_stroke);
        self.ctx.textAlign="center";
        self.ctx.fillStyle = "#000";
        self.ctx.font = "bold 11px Arial";
        self.ctx.fillText(self.rank_count[i], rbox_xoff+rank_box_wid/2, ey+rank_box_yoff+11);
      }
      rbox_xoff += rbox_xwidoff;
    }

    // rank box
    var rate = Array(8);
    var rate_accuml = 0;
    var tot = 0;
    for (var i=0; i<8; i++) { tot += self.rank_count[i]; }
    for (var i=7; i>0; i--) {
      rate_accuml += self.rank_count[i];
      rate[i] = rate_accuml/tot;
    }
    var rate_box_yoff = 10;
    var rate_box_width = 480;
    var rate_box_height = 10;
    self.ctx.fillStyle = "#fff";
    self.ctx.strokeStyle = "#666";
    self.ctx.lineWidth = 2;
    roundRect(self.ctx, x+150, ey+rate_box_yoff, rate_box_width, rate_box_height, 5, false, true);
    roundRect(self.ctx, x+150, ey+rate_box_yoff, rate_box_width, rate_box_height, 5, true, false);
    for (var i=0; i<8; i++) {
      var nw = rate_box_width * rate[i];
      if (nw == 0) continue;
      self.ctx.fillStyle = rate_fillstyle[i];
      roundRect(self.ctx, x+150+rate_box_width-nw, ey+rate_box_yoff, nw, rate_box_height, 5, true, false);
    }
  }
}





////////////////////////////////////////////////
// dark render
////////////////////////////////////////////////






function DefaultDarkRenderer(ctx) {
  var self = this;
  self.ctx = ctx;
  //alert("dark");
  // load image/resources
  var img_loadcnt = 0;
  var img_clear = new Image();
  var img_score = new Image();
  img_clear.onload = function() { img_loadcnt++; }
  img_score.onload = function() { img_loadcnt++; }
  self.isLoaded = function() { return img_loadcnt >= 2; }
  img_clear.src = "/static/img/clearlamp2dark.png";
  img_score.src = "/static/img/rank2.png";

  //
  // privates
  //
  var drawBLine = function(x1,y1,x2,y2,clr) {
    self.ctx.strokeStyle = clr!==undefined ? clr : "#000";
    self.ctx.lineWidth=1.5;
    self.ctx.moveTo(x1-0.5, y1-0.5);
    self.ctx.lineTo(x2-0.5, y2-0.5);
    self.ctx.stroke();
  };

  var drawCLine = function(x1,y1,x2,y2,clr) {
    self.ctx.strokeStyle = clr!==undefined ? clr : "#666";
    self.ctx.lineWidth=1;
    self.ctx.moveTo(x1-0.5, y1-0.5);
    self.ctx.lineTo(x2-0.5, y2-0.5);
    self.ctx.stroke();
  };

  //
  // common works
  //

  /** Theme Constants */
  self.width = 1200;
  self.colwidth = 140;
  self.itemcol = 6;
  self.itemheight = 30;
  self.margin_top = 150;
  self.margin_bottom = 100;
  self.theme_cate_margin = 0;
  self.theme_maincate_margin = 30;
  self.drawscore = true;
  self.dark = false;
  self.renderforprint = false;
  self.drawCell = function(d,x,y,w,h) {
      /*
       * INFO table function will automatically close path
       * So you don't have to do beginpath ~ closepath.
       */
      // 1 draw background
      self.ctx.fillStyle="#18181B";
      if (d.data.diff == 'H') {
        self.ctx.fillStyle="#4C4C38";
      } else if (d.data.diff == 'N') {
        self.ctx.fillStyle="#092334";
      } else if (d.data.diff == 'L') {
        self.ctx.fillStyle="#330929";
      }
      if (d.data.lvhd == 1) {
        self.ctx.fillStyle="#FFFFFF";
      }
      // 함수 인자값(검색값)이랑 곡 제목이랑 같으면
      // 배경색 변경

      self.ctx.fillRect(x,y,w,h);
      // 2 draw font
      fnt_color = "#FFF";
      if (d.data.lvhd == 1) {
        fnt_color = "#000";
      }
      curr_version = window._cur_version;
      if (!curr_version) curr_version = 99;
      if (d.data.version >= curr_version) fnt_color = "#C09ED2";
      tdrawer = new TextDrawer(self.ctx, "12px Arial", "9px Arial", fnt_color);
      tdrawer.drawText(d.data.title,x,y+h/2+4,w-35,h);
      // 3 draw border
      drawCLine(x,y,x+w,y, "#19191C");
      drawCLine(x,y+h,x+w,y+h, "#19191C");
      drawCLine(x+w,y,x+w,y+h, "#19191C");
      // 4 draw lamp
      if (d.clear > 0) {
        self.ctx.drawImage(img_clear,
            0,30 * (d.clear-1),15,30,
            x+w-15,y,15,h);
      }
      self.rank_count[d.clear]++;   // accumulate count
      // 4 score TODO
      if (self.drawscore) {
        var sx = 0;
        var sy = -1;
        var sw = 16;
        var sh = 16;
        /*
        if (d.rank == "F") sy = 116;
        else if (d.rank == "E") sy = 100;
        else if (d.rank == "D") sy = 83;
        else if (d.rank == "C") sy = 67;
        else */if (d.rank == "4") sy = 50;
        else if (d.rank == "5") sy = 33;
        else if (d.rank == "6") sy = 16;
        else if (d.rank == "7") sy = 0;
        else if (d.rank == "8"){
          sy = 132;
          sw = 21;
        }
        if (sy >= 0)
        {
          self.ctx.drawImage(img_score,
              sx,sy,sw,sh,
              x+w-40,y+9,sw,sh);
        }
      }
  }

  self.drawCategory = function(d,x,y,w,h,idx) {
    self.ctx.fillStyle="#0E0E10";
    self.ctx.fillRect(x,y,w,h);

    self.ctx.font = "bold 13px Arial";
    self.ctx.textAlign="center";
    self.ctx.fillStyle="#FFFFFF";
    self.ctx.fillText(d.category, x+w/2, y+h/2+4);

    // lamp
    var totalcnt = d.items.length;
    var clear = d.categoryclear;
    if (clear < 10 && clear > 0) {
      self.ctx.drawImage(img_clear,
          0,30 * (clear-1),15,30,
          x+w-15,y-1,14,h+1);
    }

    // border
    self.ctx.beginPath();
    drawCLine(x+w,y,x+w,y+h,"#19191C");
    drawCLine(x,y,x,y+h,"#19191C");
    // sadangborder
    drawCLine(x,y,x+w,y, "#19191C")
    self.ctx.closePath();
    if (d.categorytype == 1 && idx > 0)
    {
      self.ctx.beginPath();
      drawCLine(x,y,x+w,y, "#19191C");
      drawCLine(x,y-30,x+w,y-30, "#19191C");
      self.ctx.closePath();
    }
  }

  self.drawCategoryBox = function(d,x,y,w,h,idx) {
    self.ctx.beginPath();
    if (d.categorytype == 1 && idx > 0) {
      //drawBLine(x, y-30, x+w, y-30);
      //drawBLine(x, y-15, x+w, y-15);
    }
    self.ctx.closePath();
  }

  self.drawTableBefore = function(d,x,y,w,h) {
    var userdata = d.userdata;
    var tableinfo = d.tableinfo;

    var title = d.tableinfo.title;
    if (!title) title = d.title;
    var username = d.userdata.djname;
    if (!username) username = d.username;
    var spclass = d.userdata.spclass;
    var dpclass = d.userdata.dpclass;
    var spclassstr = d.userdata.spclassstr;
    var dpclassstr = d.userdata.dpclassstr;

    // init
    self.rank_count = [0,0,0,0,0,0,0,0];

    // 사이트 배경과 같은 색으로 채운다
    self.ctx.fillStyle = bmCanvasBackground("#1F1F23");
    self.ctx.fillRect(0, 0, self.ctx.canvas.width, self.ctx.canvas.height);

    // render tablename (as background)
    if (d.tableinfo.tablename)
    {
      self.ctx.fillStyle="#18181B";
      self.ctx.font = "bold italic 120px Arial";
      self.ctx.fillText(d.tableinfo.tablename, x+w-350, 120);
    }

    // render title
    self.ctx.font = "bold 30px Arial";
    self.ctx.textAlign="center";
    self.ctx.strokeStyle="#333";
    self.ctx.shadowColor="#000000";
    self.ctx.shadowBlur=5;
    self.ctx.miterLimit=1;
    self.ctx.lineWidth=5;
    self.ctx.strokeText(title, x+w/2, 70);
    self.ctx.shadowBlur=0;
    self.ctx.fillStyle="#EEE";
    self.ctx.fillText(title, x+w/2, 70);

    // DJ name, clear status
    self.ctx.fillStyle="#000";
    roundRect(self.ctx, x+10, 115, 100, 25, 5, true, false);
    self.ctx.font = "bold 14px Arial";
    self.ctx.textAlign="left";
    self.ctx.fillStyle="#FFF";
    self.ctx.fillText("DJ " + username, x + 20, 132);
    self.ctx.font = "bold 14px Arial";
    self.ctx.fillStyle="#FFF";
    self.ctx.fillText(d.userdata.iidxid, x + 120, 132);

    var gradecolor = [
      "#000000",
      "#000000",
      "#AADD33",  // 2
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#AADD33",
      "#3399FF",  // 9
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#3399FF",
      "#FF6666",  // 17
      "#FF6666",
      "#999999",  // 19
      "#DDDD33",  // 20
      ]
    if (spclass > 0) {
      self.ctx.fillStyle=gradecolor[spclass];
      roundRect(self.ctx, x+w-125, 115, 60, 25, {tl:5,tr:0,br:0,bl:5}, true, false);
      self.ctx.fillStyle=gradecolor[dpclass];
      roundRect(self.ctx, x+w-65, 115, 60, 25, {tl:0,tr:5,br:5,bl:0}, true, false);
      self.ctx.fillStyle="#FFF";
      self.ctx.font = "bold 14px Arial";
      self.ctx.fillText("SP" + spclassstr, x+w-120, 132);
      //self.ctx.fillText("/", x+w-68, 132);
      self.ctx.fillText("DP" + dpclassstr, x+w-60, 132);
    }

    // draw top line
    self.ctx.beginPath();
    drawBLine(x, 150, x+w, 150);
    self.ctx.closePath();
  }

  function formatDate(d) {
    var month = '' + (d.getMonth()+1);
    var day = '' + d.getDate();
    var year = d.getFullYear();
    if (month.length < 2) month = '0'+month;
    if (day.length < 2) day = '0'+day;
    return [year, month, day].join('-');
  }

  self.drawTableAfter = function(d,x,y,w,h) {
    var tabletime = d.tableinfo.time;
    var copyright = d.tableinfo.copyright;

    // very bottom line
    self.ctx.beginPath();
    drawCLine(x, y+h, x+300, y+h, "#19191C");
    self.ctx.closePath();
    y += 20;
    // date
    self.ctx.fillStyle="#999";
    self.ctx.font = "13px Arial";
    self.ctx.textAlign="right";
    var tdate = new Date(tabletime * 1000);
    self.ctx.fillText("Today: " + formatDate(new Date()) + " / Updated: " + formatDate(tdate),
        x+w, y+h+20);
    // copyright
    if (copyright) {
      self.ctx.textAlign="left";
      self.ctx.fillText(copyright, x, y+h+20);
    }


    var rate_fillstyle = ["#333333", "#686868", "#9C8D97", "#4B7A33"/*E*/, "#1B6292", "#92331B", "#92891B", "#1B8992"];
    var ey = y+h;

    // rank count
    var rank_box_wid = 35;
    var rank_box_hei = 15;
    var rank_box_yoff = 36;
    var rank_box_xoff = 150;
    var rank_box_wid_tot = 480;

    var rbox_xwidoff = (rank_box_wid_tot - rank_box_wid)/(8-1);
    var rbox_xoff = rank_box_xoff + x;
    for (var i=0; i<8; i++)
    {
      if (self.rank_count[i] > 0)
      {
        self.ctx.fillStyle = rate_fillstyle[i];
        self.ctx.strokeStyle = "#333";
        var is_stroke = false;
        if (i == 0) is_stroke = true;
        roundRect(self.ctx, rbox_xoff, ey+rank_box_yoff, rank_box_wid, rank_box_hei, 5, true, is_stroke);
        self.ctx.textAlign="center";
        self.ctx.fillStyle = "#FFF";
        self.ctx.font = "bold 11px Arial";
        self.ctx.fillText(self.rank_count[i], rbox_xoff+rank_box_wid/2, ey+rank_box_yoff+11);
      }
      rbox_xoff += rbox_xwidoff;
    }

    // rank box
    var rate = Array(8);
    var rate_accuml = 0;
    var tot = 0;
    for (var i=0; i<8; i++) { tot += self.rank_count[i]; }
    for (var i=7; i>0; i--) {
      rate_accuml += self.rank_count[i];
      rate[i] = rate_accuml/tot;
    }
    var rate_box_yoff = 10;
    var rate_box_width = 480;
    var rate_box_height = 10;
    self.ctx.fillStyle = "#333";
    self.ctx.strokeStyle = "#666";
    self.ctx.lineWidth = 2;
    roundRect(self.ctx, x+150, ey+rate_box_yoff, rate_box_width, rate_box_height, 5, false, true);
    roundRect(self.ctx, x+150, ey+rate_box_yoff, rate_box_width, rate_box_height, 5, true, false);
    for (var i=0; i<8; i++) {
      var nw = rate_box_width * rate[i];
      if (nw == 0) continue;
      self.ctx.fillStyle = rate_fillstyle[i];
      roundRect(self.ctx, x+150+rate_box_width-nw, ey+rate_box_yoff, nw, rate_box_height, 5, true, false);
    }
  }
}

# -*- coding: utf-8 -*-
import json
import re
import html
import requests
from bs4 import BeautifulSoup, NavigableString
from thefuzz import process, fuzz  # fuzz 추가
from django.db import transaction
from django.utils import timezone  # 💡 시간 갱신을 위해 추가
from playwright.sync_api import sync_playwright

# 실제 앱 이름에 맞게 수정해주세요 (예: iidxrank.models)
# 이전 에러를 바탕으로 절대 경로 임포트를 권장합니다.
from iidxrank.models import Song, RankTable, RankCategory, RankItem

# ==========================================
# [공통 유틸리티] 특수문자 및 인코딩 정제
# ==========================================
def clean_song_title(raw_title):
    """HTML 엔티티 및 불필요한 태그를 제거하고 일반 공백으로 치환합니다."""
    if not raw_title:
        return ""
    cleaned = html.unescape(raw_title)
    cleaned = cleaned.replace('\xa0', ' ') # Non-breaking space 제거
    cleaned = re.sub(r'<.*?>', '', cleaned) # HTML 태그 제거
    return cleaned.strip()

# ==========================================
# [파트 1] Textage 인피니타스 신곡 파싱 (Playwright)
# ==========================================
def fetch_infinitas_data():
    """브라우저를 실행하여 인피니타스 전용 필터링이 적용된 데이터를 추출합니다."""
    print("🌐 Textage: 인피니타스 전용 목록 추출 중...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 인피니타스 필터 파라미터(?a021B000) 적용
        page.goto("https://textage.cc/score/index.html?a021B000", wait_until="networkidle")
        
        # 브라우저 내부에서 필터링된 actbl, titletbl 변수를 JSON으로 가져옴
        js_code = 'JSON.stringify({"actbl": actbl, "titletbl": titletbl})'
        json_result = page.evaluate(js_code)
        
        browser.close()
        return json.loads(json_result)

def parse(version):
    """기본 updatedb.py에서 호출하는 곡 데이터 파싱 함수"""
    data = fetch_infinitas_data()
    actbl = data['actbl']
    titletbl = data['titletbl']
    
    musicdata = []
    print(f"✅ 인피니타스 전용 데이터 로드 완료 (총 {len(actbl)}곡).")
    
    for songid, meta in titletbl.items():
        if str(songid) not in actbl:
            continue
            
        linfo = actbl[str(songid)]
        
        # 삭제곡(0) 및 구곡(1) 필터링
        if linfo[0] == 0 or linfo[0] == 1:
            continue 

        # 채보 레벨 정보 추출 (SPN, SPH, SPA, SPL, DPN, DPH, DPA, DPL 순)
        levels = (linfo[5], linfo[7], linfo[9], linfo[11], linfo[15], linfo[17], linfo[19], linfo[21])
        title_str = clean_song_title(meta[5])
        
        # 부제목이 있는 경우 결합
        if len(meta) > 6:
            subtitle_str = clean_song_title(meta[6])
            if subtitle_str:
                title_str = f"{title_str} {subtitle_str}"
                
        playtypes = ('SPN', 'SPH', 'SPA', 'SPL', 'DPN', 'DPH', 'DPA', 'DPL')
        obj_id = 100000 + meta[1]
        
        for lvl, playtype in zip(levels, playtypes):
            if lvl < 10: # 레벨 10 이상만 DB에 저장
                continue
                
            musicdata.append({
                'title': title_str,
                'level': lvl,
                'version': version,
                'clear': 0,
                'score': 0,
                'notes': 0,
                'miss': 0,
                'id': obj_id,
                'diff': playtype
            })
            
    return musicdata

# ==========================================
# [파트 2] 구글 시트 서열표 자동 분류 (BeautifulSoup)
# ==========================================
class IIDXSheetParser:
    def __init__(self):
        # 웹에 게시된 구글 시트 URL
        self.base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSUdp6iuEzE8Z5AL1hkoxzLexp89nJnLQMmICm6_MC0_UjCp1ImZFzabcZkvCpK7mcWvm_2t6iYoJRg/pubhtml"
        
        # 업데이트할 대상 시트 리스트
        self.target_sheets = [
            {
                # SP12H
                "table_name": "SP12H",
                "table_title": "SP12H",
                "url": f"{self.base_url}?gid=1277599511&single=true",
                "level": 12,
                "default_type": "SPA"
            },
            {
                # SP12N
                "table_name": "SP12N",
                "table_title": "SP12N",
                "url": f"{self.base_url}?gid=1184656976&single=true",
                "level": 12,
                "default_type": "SPA"
            }
        ]
        
        # 유사도 매칭을 위해 DB의 모든 곡 제목을 캐싱
        self.db_titles = list(Song.objects.values_list('songtitle', flat=True).distinct())
        self.match_threshold = 85

    def _get_red_classes(self, soup):
        red_classes = []
        for style_tag in soup.find_all('style'):
            if not style_tag.string:
                continue
                
            pattern = r'\.(s\d+)[^{]*\{[^}]*color:\s*(#ff0000|#f00|red|#ea4335|#cc0000|#e60000)'
            matches = re.findall(pattern, style_tag.string, re.IGNORECASE)
            red_classes.extend([m[0] for m in matches])
            
        return list(set(red_classes))

    def process_sheet(self, sheet_info, mode):
        print(f"\n🚀 [{sheet_info['table_title']}] 시트 매핑 프로세스 시작 (모드: {mode})...")
        
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()
                
                target_url = sheet_info['url'] + "&headers=false&chrome=false&widget=false"
                page.goto(target_url, wait_until="networkidle")
                
                html_content = ""
                for frame in page.frames:
                    try:
                        if frame.query_selector("table.waffle"):
                            html_content = frame.content()
                            break
                    except Exception:
                        continue
                
                if not html_content:
                    html_content = page.content()
                browser.close()

            soup = BeautifulSoup(html_content, 'html.parser')

        except Exception as e:
            print(f"❌ 시트 로드 실패: {e}")
            return

        red_classes = self._get_red_classes(soup)
        waffle_table = soup.find('table', class_='waffle')
        rows = waffle_table.find_all('tr') if waffle_table else soup.find_all('tr')
        
        if not rows or len(rows) < 2:
            print("❌ 테이블 데이터를 찾을 수 없습니다.")
            return

        headers = {} 
        parsed_data = {}  # DB 저장을 위해 메모리에 임시 보관
        fail_count = 0

        # ----------------------------------------------------
        # 1단계: 시트 파싱 및 메모리 저장
        # ----------------------------------------------------
        print("🔍 구글 시트 데이터를 분석 중입니다...")
        for row in rows:
            cells = row.find_all(['td', 'th'])
            for col_idx, cell in enumerate(cells):
                
                lines = []
                current_text = ""
                is_red = False
                cell_classes = cell.get('class', [])
                
                for child in cell.descendants:
                    if child.name in ['br', 'div']:
                        if current_text.strip():
                            lines.append((current_text.strip(), is_red))
                        current_text = ""
                        is_red = False
                    elif isinstance(child, NavigableString):
                        text_parts = str(child).split('\n')
                        for i, part in enumerate(text_parts):
                            if i > 0: 
                                if current_text.strip():
                                    lines.append((current_text.strip(), is_red))
                                current_text = ""
                                is_red = False
                            
                            if part:
                                current_text += part 
                                parent = child.parent
                                parent_classes = parent.get('class', []) if parent else []
                                parent_style = parent.get('style', '').lower() if parent else ''
                                all_classes = set(parent_classes + cell_classes)
                                
                                if any(c in red_classes for c in all_classes) or \
                                   '#ff0000' in parent_style or '#f00' in parent_style or 'red' in parent_style or \
                                   '#cc0000' in parent_style or '#ea4335' in parent_style or '#e60000' in parent_style:
                                    is_red = True
                                    
                if current_text.strip():
                    lines.append((current_text.strip(), is_red))

                for raw_title, song_is_red in lines:
                    raw_title = raw_title.strip()
                    if not raw_title: 
                        continue

                    if col_idx not in headers:
                        if len(raw_title) < 15:
                            headers[col_idx] = raw_title
                        continue

                    # 💡 A, F 수동 분류 보호 로직
                    # 이 코드로 인해 실제 A, F 곡들이 시트 파싱에서 건너뛰어지고 DB 상에서는 Type 2(수동유지)가 됩니다.
                    if raw_title in headers.values():
                        continue

                    clean_title = raw_title.replace("[L]", "").replace("[H]", "").strip()
                    song_type = sheet_info['default_type']
                    if "[L]" in raw_title: song_type = "SPL"
                    elif "[H]" in raw_title: song_type = "SPH"

                    match_result = process.extractOne(clean_title, self.db_titles, scorer=fuzz.ratio)
                    
                    if match_result and match_result[1] >= self.match_threshold:
                        matched_title, score = match_result
                        target_song = Song.objects.filter(songtitle=matched_title, songtype=song_type).first()

                        if target_song:
                            raw_header = headers.get(col_idx, "?")
                            column_header = raw_header.replace('＋', '+').strip()
                            category_prefix = "개인차" if song_is_red else "지력"
                            target_category_name = f"{category_prefix} {column_header}"

                            tier_base_scores = {
                                "S+": 28.0, "S": 26.0, "A+": 24.0, "A": 22.0,
                                "B+": 20.0, "B": 18.0, "C": 16.0, "D": 14.0,
                                "E": 12.0, "F": 10.0
                            }
                            base_score = tier_base_scores.get(column_header.upper(), 10.0)
                            c_type = 0 if song_is_red else 1
                            c_sort = base_score + float(c_type)

                            parsed_data[target_song.id] = {
                                'song': target_song,
                                'cat_name': target_category_name,
                                'c_type': c_type,
                                'c_sort': c_sort,
                                'score': score
                            }
                        else:
                            fail_count += 1
                    else:
                        fail_count += 1

        # ----------------------------------------------------
        # 2단계: DB 갱신 분기 (RESET / UPDATE)
        # ----------------------------------------------------
        with transaction.atomic():
            rank_table, _ = RankTable.objects.get_or_create(
                tablename=sheet_info['table_name'],
                defaults={
                    'tabletitle': sheet_info['table_title'],
                    'level': sheet_info['level'],
                    'type': sheet_info['default_type']
                }
            )

            # --- [RESET 모드] ---
            if mode == "RESET":
                print(f"\n🧹 [초기화] 테이블 '{sheet_info['table_name']}'의 데이터를 모두 비우고 다시 작성합니다...")
                RankItem.objects.filter(rankcategory__ranktable=rank_table).delete()
                RankCategory.objects.filter(ranktable=rank_table).delete()
                
                new_count = 0
                for sid, data in parsed_data.items():
                    category, _ = RankCategory.objects.get_or_create(
                        ranktable=rank_table,
                        categoryname=data['cat_name'],
                        defaults={'categorytype': data['c_type'], 'sortindex': data['c_sort']}
                    )
                    RankItem.objects.create(rankcategory=category, song=data['song'], info=f"Auto-mapped ({data['score']}%)")
                    new_count += 1
                
                rank_table.time = timezone.now()
                rank_table.save()
                print(f"✅ 초기화 완료: {new_count}곡 새로 매핑됨. (실패 {fail_count}건)")
                return

            # --- [UPDATE 모드] ---
            current_items = {item.song_id: item for item in RankItem.objects.filter(rankcategory__ranktable=rank_table).select_related('rankcategory', 'song')}
            
            type_0_new = []
            type_1_updates = []
            type_2_missing = []

            for sid, p_data in parsed_data.items():
                if sid not in current_items:
                    type_0_new.append(p_data)
                else:
                    db_item = current_items[sid]
                    if db_item.rankcategory.categoryname != p_data['cat_name']:
                        type_1_updates.append({'item': db_item, 'old_cat': db_item.rankcategory.categoryname, 'new_data': p_data})

            for sid, db_item in current_items.items():
                if sid not in parsed_data:
                    cat_name = db_item.rankcategory.categoryname
                    # 전용곡/삭제곡은 제외
                    if not ("INFINITAS" in cat_name.upper() and "전용" in cat_name) and "AC 삭제" not in cat_name:
                        type_2_missing.append(db_item)

            print("\n" + "="*60)
            
            # [Type 0] 
            for d in type_0_new:
                cat, _ = RankCategory.objects.get_or_create(
                    ranktable=rank_table, categoryname=d['cat_name'],
                    defaults={'categorytype': d['c_type'], 'sortindex': d['c_sort']}
                )
                RankItem.objects.create(rankcategory=cat, song=d['song'], info=f"Added via Update ({d['score']}%)")
            print(f"✅ [Type 0] 미분류에서 갱신(새로 추가)된 곡: {len(type_0_new)}곡")

            # [Type 1] 
            updated_count = 0
            if type_1_updates:
                print(f"\n⚠️ [Type 1] 서열표 안에서 위치가 변경된 곡들이 있습니다 ({len(type_1_updates)}건).")
                print("-" * 60)
                for idx, update in enumerate(type_1_updates, 1):
                    song = update['item'].song
                    print(f"  [{idx}] {song.songtitle} ({song.songtype})")
                    print(f"      {update['old_cat']} ➔ {update['new_data']['cat_name']}")
                
                print("-" * 60)

                # CLI 에서는 예전 그대로 input() 을 쓰고, 웹 대시보드에서 돌고 있으면
                # 질문을 DB 에 써 두고 답을 기다린다. update/prompt.py 참조.
                from update import prompt as _prompt
                _choices = []
                for _i, _u in enumerate(type_1_updates, 1):
                    _song = _u['item'].song
                    _choices.append({
                        'value': str(_i),
                        'label': '%s (%s)' % (_song.songtitle, _song.songtype),
                        'detail': '%s ➜ %s' % (_u['old_cat'],
                                                    _u['new_data']['cat_name']),
                    })
                choice = _prompt.ask(
                    question='[%s] 위치가 변경된 곡 %d건을 적용할까요?'
                             % (sheet_info['table_title'], len(type_1_updates)),
                    choices=_choices,
                    kind='multi',
                    default='',
                    help='체크한 곡만 새 카테고리로 옮깁니다. 아무것도 고르지 않고 '
                         '넘기면 이번 회차에는 전부 기존 분류를 유지합니다.',
                    cli_prompt="\n🔄 변경을 적용할 번호를 입력하세요 "
                               "(쉼표(,)로 구분 / 전부 'all' / 넘기려면 Enter): ",
                ).strip()
                
                if choice.lower() == 'all':
                    indices = list(range(1, len(type_1_updates) + 1))
                elif choice:
                    try:
                        indices = [int(x.strip()) for x in choice.split(',')]
                    except ValueError:
                        print("❌ 잘못된 입력입니다. 갱신을 건너뜁니다.")
                        indices = []
                else:
                    indices = []

                for i in indices:
                    if 1 <= i <= len(type_1_updates):
                        u_data = type_1_updates[i-1]
                        item = u_data['item']
                        n_data = u_data['new_data']
                        
                        cat, _ = RankCategory.objects.get_or_create(
                            ranktable=rank_table, categoryname=n_data['cat_name'],
                            defaults={'categorytype': n_data['c_type'], 'sortindex': n_data['c_sort']}
                        )
                        item.rankcategory = cat
                        item.info = f"Updated via CLI ({n_data['score']}%)"
                        item.save()
                        updated_count += 1
                
                print(f"   => 🎯 [승인 완료] 총 {updated_count}곡 위치가 변경되었습니다.")

            # [Type 2] 
            if type_2_missing:
                print(f"\n❌ [Type 2] 서열표엔 존재하나 시트에서 안 보이는 곡 (기존 분류 유지): {len(type_2_missing)}곡")
                for item in type_2_missing:
                    print(f"  - {item.song.songtitle} ({item.song.songtype}) [현재: {item.rankcategory.categoryname}]")

            # 시간 갱신
            rank_table.time = timezone.now()
            rank_table.save()
            
            print("\n" + "="*60)
            print(f"🎉 갱신(UPDATE) 프로세스 완료 (테이블 시간 갱신됨: {rank_table.time.strftime('%Y-%m-%d %H:%M:%S')})")
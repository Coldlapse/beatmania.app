# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from iidxrank.models import RankTable, RankItem

class Command(BaseCommand):
    help = 'SP12TEST와 SP12H 서열표의 분류 결과를 대조하고 오차를 분석합니다.'

    def handle(self, *args, **options):
        table_new_name = 'SP12TEST'
        table_old_name = 'SP12H'

        self.stdout.write(self.style.SUCCESS(f"\n🔍 [{table_new_name}] vs [{table_old_name}] 데이터 대조 및 오차 분석을 시작합니다...\n"))

        try:
            table_new = RankTable.objects.get(tablename=table_new_name)
            table_old = RankTable.objects.get(tablename=table_old_name)
        except RankTable.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"❌ 테이블을 찾을 수 없습니다: {e}"))
            return

        def get_song_mapping(rank_table):
            mapping = {}
            items = RankItem.objects.filter(rankcategory__ranktable=rank_table).select_related('song', 'rankcategory')
            for item in items:
                cat_name = item.rankcategory.categoryname.strip()
                
                # 💡 수정: "INFINITAS 전용 곡"은 난이도가 배정되지 않은 상태이므로 아예 매핑에서 제외(무시)합니다.
                if "INFINITAS" in cat_name.upper() and "전용" in cat_name:
                    continue 
                    
                mapping[item.song.id] = {
                    'title': item.song.songtitle,
                    'type': item.song.songtype,
                    'category': cat_name
                }
            return mapping

        # 양쪽 테이블의 데이터를 딕셔너리로 로드
        new_map = get_song_mapping(table_new)
        old_map = get_song_mapping(table_old)

        all_song_ids = set(new_map.keys()).union(set(old_map.keys()))

        match_count = 0
        diff_list = []
        only_new_list = []
        only_old_list = []

        # 💡 핵심 로직: 곡 ID를 기준으로 양쪽 카테고리 1:1 대조
        for sid in all_song_ids:
            in_new = sid in new_map
            in_old = sid in old_map

            if in_new and in_old:
                cat_new = new_map[sid]['category']
                cat_old = old_map[sid]['category']

                if cat_new == cat_old:
                    match_count += 1
                else:
                    diff_list.append({
                        'title': new_map[sid]['title'],
                        'type': new_map[sid]['type'],
                        'cat_new': cat_new,
                        'cat_old': cat_old
                    })
            elif in_new:
                only_new_list.append(new_map[sid])
            elif in_old:
                only_old_list.append(old_map[sid])

        # 보기 좋게 곡명 기준으로 정렬
        diff_list.sort(key=lambda x: x['title'].lower())
        only_new_list.sort(key=lambda x: x['title'].lower())
        only_old_list.sort(key=lambda x: x['title'].lower())

        # ==========================================
        # 📊 분석 결과 출력 파트
        # ==========================================
        total_songs = len(all_song_ids)
        self.stdout.write(f"총 분석 대상 곡: {total_songs}곡\n")
        print("=" * 70)
        
        # 1. 오차 내역 (위치가 다름)
        if diff_list:
            self.stdout.write(self.style.WARNING(f"⚠️ 카테고리 불일치 (오차 발생): {len(diff_list)}곡"))
            print("-" * 70)
            for d in diff_list:
                title_str = f"{d['title']} ({d['type']})"
                # 구버전(SP12H) -> 신버전(SP12TEST) 순으로 변화량 표시
                print(f" {title_str:<40} | {d['cat_old']:<10} ➔  {d['cat_new']}")
            print("=" * 70)
        
        # 2. 신규 파서에서만 잡힌 곡 (SP12TEST에만 존재)
        if only_new_list:
            self.stdout.write(self.style.SUCCESS(f"✅ 신규 등록/감지됨 ({table_new_name}에만 존재): {len(only_new_list)}곡"))
            print("-" * 70)
            for d in only_new_list:
                print(f" + {d['title']} ({d['type']})  [배치: {d['category']}]")
            print("=" * 70)

        # 3. 신규 파서에서 놓친 곡 (SP12H에만 존재)
        if only_old_list:
            self.stdout.write(self.style.ERROR(f"❌ 누락/미감지됨 ({table_old_name}에만 존재): {len(only_old_list)}곡"))
            print("-" * 70)
            for d in only_old_list:
                print(f" - {d['title']} ({d['type']})  [기존: {d['category']}]")
            print("=" * 70)

        # 요약 리포트
        accuracy = (match_count / total_songs) * 100 if total_songs > 0 else 0
        self.stdout.write(self.style.SUCCESS(f"📈 최종 분석 요약"))
        print(f" - 완벽 일치: {match_count}곡")
        print(f" - 일치율: {accuracy:.2f}%")
        print("=" * 70)
# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from iidxrank.models import Song
from thefuzz import fuzz
from collections import defaultdict
import sys

class Command(BaseCommand):
    help = '유사도 분석을 통해 중복 등록된 곡을 찾아 대화형으로 삭제합니다.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 데이터베이스에서 곡 데이터를 불러오는 중..."))
        
        all_songs = list(Song.objects.all())
        songs_by_type = defaultdict(list)
        
        # 1. 타입별(SPA, SPL 등)로 곡 분류 (비교 연산 최적화)
        for song in all_songs:
            songs_by_type[song.songtype].append(song)
            
        self.stdout.write(f"✅ 총 {len(all_songs)}개의 곡을 로드했습니다. 유사도 검사를 시작합니다...\n")

        suspicious_groups = []
        processed_ids = set()

        # 2. 유사도 기반 중복 의심 그룹 색출
        for song_type, type_songs in songs_by_type.items():
            for i in range(len(type_songs)):
                song_a = type_songs[i]
                if song_a.id in processed_ids:
                    continue

                current_group = [song_a]
                for j in range(i + 1, len(type_songs)):
                    song_b = type_songs[j]
                    if song_b.id in processed_ids:
                        continue

                    # 형태가 다르거나(전각/반각), 특수문자가 달라도 높은 유사도를 반환하도록 ratio 사용
                    score = fuzz.ratio(song_a.songtitle, song_b.songtitle)
                    
                    # 유사도가 80% 이상이면 같은 곡의 변형으로 의심
                    if score >= 80:
                        current_group.append(song_b)

                # 중복이 발견된 경우 그룹에 추가
                if len(current_group) > 1:
                    suspicious_groups.append(current_group)
                    for s in current_group:
                        processed_ids.add(s.id)

        total_groups = len(suspicious_groups)
        if total_groups == 0:
            self.stdout.write(self.style.SUCCESS("🎉 중복으로 의심되는 곡이 없습니다! 데이터베이스가 깔끔합니다."))
            return

        self.stdout.write(self.style.WARNING(f"⚠️ 총 {total_groups}개의 중복 의심 그룹이 발견되었습니다.\n"))

        # 3. 대화형 컨펌 루프
        deleted_count = 0
        for idx, group in enumerate(suspicious_groups, 1):
            print("-" * 60)
            print(f"[{idx} / {total_groups}] 🎵 패턴: {group[0].songtype}")
            
            # 그룹 내의 곡들 출력
            for i, song in enumerate(group, 1):
                print(f"  [{i}] ID: {song.id:<10} | 제목: {song.songtitle}")

            while True:
                # CLI 에서는 예전 그대로 input(), 웹 대시보드에서는 DB 를 경유해
                # 묻는다. update/prompt.py 참조.
                from update import prompt as _prompt
                _choices = [{
                    'value': str(_i),
                    'label': _song.songtitle,
                    'detail': 'ID %s · %s' % (_song.id, _song.songtype),
                } for _i, _song in enumerate(group, 1)]
                choice = _prompt.ask(
                    question='[%d/%d] 중복 의심 그룹 (%s) — 삭제할 곡을 고르세요'
                             % (idx, total_groups, group[0].songtype),
                    choices=_choices,
                    kind='multi',
                    default='',
                    help='체크한 곡을 삭제합니다. 연결된 서열표 항목도 함께 사라집니다. '
                         '되돌릴 수 없으니 신중히 고르세요. 아무것도 안 고르면 건너뜁니다.',
                    cli_prompt="\n🗑️  삭제할 번호를 입력하세요 "
                               "(여러 개면 쉼표(,)로 구분 / 건너뛰려면 Enter): ",
                ).strip()
                
                if not choice:
                    print("⏭️  건너뜁니다.\n")
                    break
                
                try:
                    # 입력받은 번호 파싱
                    indices_to_delete = [int(x.strip()) for x in choice.split(',')]
                    songs_to_delete = []
                    
                    for i in indices_to_delete:
                        if 1 <= i <= len(group):
                            songs_to_delete.append(group[i-1])
                        else:
                            raise ValueError(f"{i}는 잘못된 번호입니다.")

                    # 삭제 진행 (Django ORM의 CASCADE로 인해 연결된 서열표 랭크아이템도 자동 삭제됨)
                    for song in songs_to_delete:
                        song_id = song.id
                        song_title = song.songtitle
                        song.delete()
                        deleted_count += 1
                        print(f"   => 💥 [삭제 완료] ID: {song_id} ({song_title})")
                    print()
                    break

                except ValueError as e:
                    print(f"❌ 입력 오류: {e}. 다시 입력해 주세요.")
                except Exception as e:
                    print(f"❌ DB 삭제 중 오류 발생: {e}")
                    break

        print("=" * 60)
        self.stdout.write(self.style.SUCCESS(f"✅ 정리 완료! 총 {deleted_count}개의 중복 곡이 삭제되었습니다."))
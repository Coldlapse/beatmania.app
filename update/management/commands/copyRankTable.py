# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from iidxrank.models import RankTable, RankCategory, RankItem

class Command(BaseCommand):
    help = 'SP12H 서열표의 모든 카테고리와 곡 배치 데이터를 SP12TEST로 그대로 복사합니다.'

    def handle(self, *args, **options):
        src_tablename = 'SP12H'
        dest_tablename = 'SP12TEST'

        self.stdout.write(self.style.SUCCESS(f"📦 [{src_tablename}] ➔ [{dest_tablename}] 데이터 복제 프로세스를 시작합니다..."))

        # 1. 원본 테이블(SP12H) 존부 확인
        try:
            src_table = RankTable.objects.get(tablename=src_tablename)
        except RankTable.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 원본 테이블({src_tablename})을 찾을 수 없습니다. 명칭을 확인해 주세요."))
            return

        with transaction.atomic():
            # 2. 대상 테이블(SP12TEST) 가져오기 또는 원본 설정을 기반으로 신규 생성
            dest_table, created = RankTable.objects.get_or_create(
                tablename=dest_tablename,
                defaults={
                    'tabletitle': f"{src_table.tabletitle} (복사본)",
                    'level': src_table.level,
                    'type': src_table.type,
                    'time': timezone.now()
                }
            )

            # 3. 데이터가 꼬이는 것을 막기 위해 대상 테이블의 기존 데이터 먼저 완전 초기화
            self.stdout.write(f"🧹 대상 테이블 [{dest_tablename}]의 기존 카테고리 및 아이템을 완전히 청소합니다...")
            RankItem.objects.filter(rankcategory__ranktable=dest_table).delete()
            RankCategory.objects.filter(ranktable=dest_table).delete()

            # 4. 원본 테이블의 모든 카테고리 순회하며 복사
            src_categories = RankCategory.objects.filter(ranktable=src_table)
            category_count = 0
            item_count = 0

            for src_cat in src_categories:
                # 원본 카테고리의 속성(이름, 타입, 정렬 인덱스)을 그대로 복제하여 생성
                dest_cat = RankCategory.objects.create(
                    ranktable=dest_table,
                    categoryname=src_cat.categoryname,
                    categorytype=src_cat.categorytype,
                    sortindex=src_cat.sortindex
                )
                category_count += 1

                # 5. 해당 카테고리에 속한 곡 아이템(RankItem)들을 대량(Bulk) 복사
                src_items = RankItem.objects.filter(rankcategory=src_cat)
                bulk_items = []
                
                for src_item in src_items:
                    bulk_items.append(
                        RankItem(
                            rankcategory=dest_cat,
                            song=src_item.song,
                            info=src_item.info
                        )
                    )
                
                if bulk_items:
                    RankItem.objects.bulk_create(bulk_items)
                    item_count += len(bulk_items)

            # 6. 복사가 완료된 후 대상 테이블의 갱신 시각을 현재로 업데이트
            dest_table.time = timezone.now()
            dest_table.save()

            print("=" * 60)
            self.stdout.write(self.style.SUCCESS(
                f"✅ 복사 완료! 생성된 카테고리: {category_count}개 / 복사된 곡 아이템: {item_count}개"
            ))
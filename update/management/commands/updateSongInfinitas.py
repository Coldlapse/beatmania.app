# -*- coding: utf-8 -*-
from django.core.management import BaseCommand
import iidxrank.models as models
import update.updatedb as updatedb
from update.parser_infinitas import IIDXSheetParser
import traceback  # 상세 에러 추적을 위해 추가

class Command(BaseCommand):
    help = "update all song db from textage.cc and map to ranktable"

    def add_arguments(self, parser):
        parser.add_argument('--set_version', type=int, help='specific version of song version')
        parser.add_argument('--test', type=int, help='only for test (not actually update record)')
        # 💡 추가된 인수: 초기화 모드와 갱신 모드
        parser.add_argument('--reset', action='store_true', help='기존 서열표 데이터를 모두 날리고 처음부터 매핑합니다.')
        parser.add_argument('--update', action='store_true', help='기존 데이터를 보존하며 변동된 곡만 갱신합니다.')

    def handle(self, *args, **options):
        # 인수 유효성 검사 (reset, update 중 하나는 반드시 있어야 함)
        if not options.get('reset') and not options.get('update'):
            self.stdout.write(self.style.ERROR("❌ 실행 인수가 없습니다. 명령어 뒤에 '--reset' 또는 '--update'를 붙여주세요."))
            return
        
        if options.get('reset') and options.get('update'):
            self.stdout.write(self.style.ERROR("❌ '--reset'과 '--update'를 동시에 사용할 수 없습니다."))
            return

        mode = "RESET" if options.get('reset') else "UPDATE"
        version = -1
        if options.get('set_version'):
            version = options['set_version']
        if options.get('test'):
            updatedb.TEST = options['test']
        
        self.stdout.write(self.style.SUCCESS("1️⃣ Textage 곡 데이터(Song) 업데이트를 시작합니다..."))
        updatedb.update_from_infinitas(version)

        self.stdout.write(self.style.SUCCESS(f"\n2️⃣ 구글 시트 서열표(RankTable) [{mode} 모드] 매핑을 시작합니다..."))
        
        if not options.get('test'):
            try:
                parser = IIDXSheetParser()
                for sheet in parser.target_sheets:
                    # 💡 mode 매개변수를 추가로 넘겨줍니다.
                    parser.process_sheet(sheet, mode)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ 서열표 매핑 중 오류 발생:\n{traceback.format_exc()}"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ 테스트 모드이므로 서열표 매핑은 건너뜁니다."))

        self.stdout.write(self.style.SUCCESS("\n✅ 모든 프로세스가 완료되었습니다!"))
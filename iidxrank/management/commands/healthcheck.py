# -*- coding: utf-8 -*-
"""상태 점검을 한 번 돌려 결과를 남긴다.

cron 이나 systemd timer 로 주기적으로 부른다. 5분 간격을 기준으로 잡았다.

    */5 * * * * cd /srv/beatmania && python manage.py healthcheck

화면(서비스 현황)은 이 명령이 남긴 것만 읽는다. 요청이 올 때마다 외부에
붙어 보면 느리고 상대에게도 실례다.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from iidxrank import health
from iidxrank.models import HealthCheck

# 얼마나 남길 것인가. 5분 간격이면 30일이 대상 하나당 8,640행이다.
KEEP_DAYS = 30


class Command(BaseCommand):
    help = '사이트/DB/외부 페이지 상태를 점검하고 기록한다'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='결과를 저장하지 않고 화면에만 출력한다')
        parser.add_argument('--keep-days', type=int, default=KEEP_DAYS,
                            help='이보다 오래된 기록을 지운다 (기본 %d)' % KEEP_DAYS)

    def handle(self, *args, **options):
        results = health.run_all()

        for r in results:
            mark = {'ok': 'OK  ', 'degraded': 'WARN', 'down': 'DOWN'}[r['status']]
            self.stdout.write('%s %-10s %5dms %s'
                              % (mark, r['target'], r['latency_ms'], r['note']))

        if options['dry_run']:
            self.stdout.write('(--dry-run: 저장하지 않음)')
            return

        HealthCheck.objects.bulk_create([
            HealthCheck(target=r['target'], status=r['status'],
                        latency_ms=r['latency_ms'], note=r['note'][:200],
                        checked_at=r['checked_at'])
            for r in results])

        cutoff = timezone.now() - timezone.timedelta(days=options['keep_days'])
        removed, _ = HealthCheck.objects.filter(checked_at__lt=cutoff).delete()
        if removed:
            self.stdout.write('오래된 기록 %d건 삭제' % removed)

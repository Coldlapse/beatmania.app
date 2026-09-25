# -*- coding: utf-8 -*-
"""cpi.makecir.com 의 채보별 CPI 값을 받아 둔다. 하루 한 번 cron 으로 돈다.

    python manage.py update_cpi
"""
from django.core.management.base import BaseCommand, CommandError

from iidxrank import cpi


class Command(BaseCommand):
    help = 'cpi.makecir.com 에서 SP☆12 채보별 CPI 값을 받아 온다(하루 한 번).'

    def handle(self, *args, **options):
        if not cpi.ENABLED:
            self.stdout.write('CPI 가 꺼져 있어 받지 않습니다 (iidxrank/cpi.py ENABLED).')
            return
        try:
            r = cpi.fetch_and_store()
        except Exception as e:
            raise CommandError('CPI 값을 받지 못했습니다: %s' % e)
        self.stdout.write('CPI 채보 %d개 중 %d개 반영, 곡 DB 에 없는 채보 %d개'
                          % (r['charts'], r['matched'], len(r['missing'])))

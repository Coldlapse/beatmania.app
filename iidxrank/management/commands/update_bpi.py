# -*- coding: utf-8 -*-
"""BPIManager(bpi2.poyashi.me)의 채보별 BPI V2 값을 받아 둔다. 하루 한 번 cron 으로 돈다.

    python manage.py update_bpi
"""
from django.core.management.base import BaseCommand, CommandError

from iidxrank import bpi


class Command(BaseCommand):
    help = 'bpi2.poyashi.me 에서 SP☆11·12 채보별 BPI 값을 받아 온다(하루 한 번).'

    def handle(self, *args, **options):
        if not bpi.ENABLED:
            self.stdout.write('BPI 가 꺼져 있어 받지 않습니다 (iidxrank/bpi.py ENABLED).')
            return
        try:
            r = bpi.fetch_and_store()
        except Exception as e:
            raise CommandError('BPI 값을 받지 못했습니다: %s' % e)
        self.stdout.write('BPI 채보 %d개(☆12 %d개) 중 %d개 곡 DB 와 연결, 못 찾은 채보 %d개'
                          % (r['charts'], r['level12'], r['matched'], len(r['missing'])))
        for m in r['missing'][:40]:
            self.stdout.write('  - ' + m)

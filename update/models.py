from __future__ import unicode_literals

from django.db import models
import iidxrank.models

# User / UserRecord / SongCalc.

class PlayerCalc(models.Model):
    player = models.OneToOneField(iidxrank.models.Player, on_delete=models.CASCADE)
    tag = models.CharField(max_length=20)

    valid = models.IntegerField(default=0)  # if no fail, then it's invalid; can't calculate
    sp_l = models.FloatField(default=0)
    sp_w = models.FloatField(default=0)
    dp_l = models.FloatField(default=0)
    dp_w = models.FloatField(default=0)

class SongCalc(models.Model):
    song = models.OneToOneField(iidxrank.models.Song, on_delete=models.CASCADE)
    tag = models.CharField(max_length=20)

    valid = models.IntegerField(default=0)  # if no fail, then it's invalid; can't calculate
    ez_l = models.FloatField(default=0)
    ez_w = models.FloatField(default=0)
    nm_l = models.FloatField(default=0)
    nm_w = models.FloatField(default=0)
    hd_l = models.FloatField(default=0)
    hd_w = models.FloatField(default=0)
    ex_l = models.FloatField(default=0)
    ex_w = models.FloatField(default=0)
    fc_l = models.FloatField(default=0)
    fc_w = models.FloatField(default=0)

    score_avg = models.FloatField(default=0)


class CommandRun(models.Model):
    """관리자 대시보드에서 실행한 management command 한 건의 기록.

    로그를 메모리가 아니라 DB 에 쌓는 이유: mod_wsgi 는 워커 프로세스가 여러 개라
    실행을 시작한 워커와 로그를 폴링하는 요청을 받는 워커가 다를 수 있다.
    """
    PENDING = 'pending'
    RUNNING = 'running'
    WAITING = 'waiting'      # 사용자의 답을 기다리는 중
    SUCCESS = 'success'
    FAILED = 'failed'
    STATUS_CHOICES = [
        (PENDING, '대기'), (RUNNING, '실행 중'), (WAITING, '입력 대기'),
        (SUCCESS, '성공'), (FAILED, '실패'),
    ]

    command = models.CharField(max_length=64)
    # 실제로 넘긴 옵션. 표시용이자 감사 기록이다.
    options = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    # 누가 돌렸는지 남긴다. 사용자가 지워져도 기록은 유지한다.
    started_by = models.ForeignKey(
        'auth.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='command_runs')
    log = models.TextField(blank=True, default='')

    # --- 대화형 프롬프트 -----------------------------------------------------
    # 명령이 CLI 에서 input() 으로 묻던 것을 웹에서도 받기 위한 자리.
    # 실행 스레드는 prompt 를 써 놓고 answer 가 채워질 때까지 폴링하며 기다린다.
    # DB 를 쓰는 이유는 로그와 같다 — 묻는 워커와 답을 받는 워커가 다를 수 있다.
    prompt = models.TextField(blank=True, default='')          # JSON
    prompt_answer = models.TextField(blank=True, default='')   # 사용자가 고른 값
    prompt_asked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return '%s %s (%s)' % (self.command, self.options, self.status)

    @property
    def is_done(self):
        return self.status in (self.SUCCESS, self.FAILED)

    @property
    def is_active(self):
        """아직 잠금을 쥐고 있는 상태인가."""
        return self.status in (self.PENDING, self.RUNNING, self.WAITING)

    def prompt_data(self):
        import json
        if not self.prompt:
            return None
        try:
            return json.loads(self.prompt)
        except ValueError:
            return None

    @property
    def duration_seconds(self):
        if not self.finished_at:
            return None
        return int((self.finished_at - self.started_at).total_seconds())

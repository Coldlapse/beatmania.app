# lets refer: https://docs.djangoproject.com/en/1.9/intro/tutorial07/
# http://www.b-list.org/weblog/2007/sep/22/standalone-django-scripts/

from datetime import datetime, date
from django.db import models    # whether to use django?
from django.db.models import CASCADE
from django.conf import settings
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from hitcount.models import HitCount
import os
import secrets # 파이썬 내장 라이브러리
import uuid


def avatar_upload_to(instance, filename):
    """업로드 파일명을 그대로 쓰지 않는다.

    사용자가 준 이름에는 경로 조작(../)·스크립트 확장자·다른 사람의 이름이
    들어올 수 있다. 확장자만 화이트리스트에서 고르고 이름은 새로 만든다.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
        ext = '.png'
    return 'avatar/%s%s' % (uuid.uuid4().hex, ext)

# 1. API 인증을 위한 커스텀 토큰 모델
class ApiToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_token')
    key = models.CharField(max_length=40, unique=True, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 객체가 처음 생성될 때만 토큰 키를 생성합니다.
        if not self.key:
            self.key = secrets.token_hex(20)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.key

# 2. 날짜별 타건 기록을 저장할 모델 (스케줄러가 필요 없는 방식)
class TypingLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='typing_logs')
    count = models.IntegerField(default=0, verbose_name="총 타건 수")
    date = models.DateField(verbose_name="날짜")

    class Meta:
        # 한 사용자는 하루에 하나의 로그만 갖도록 제약 조건 설정
        unique_together = ('user', 'date')
        ordering = ['-date'] # 최신 날짜순으로 정렬

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.count}타)"
        
class Song(models.Model):
    songid = models.IntegerField(default=0)
    songtype = models.CharField(max_length=8)       # dph/spa ...
    songtitle = models.CharField(max_length=100)
    songlevel = models.IntegerField(default=0)
    songnotes = models.IntegerField(default=0)
    version = models.CharField(max_length=20)

    songid_iidxme = models.IntegerField(default=0)

    # used with DBM/DBR,
    # and it'll update itself when original song record is updated.
    original = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    # TODO: add iidx song english name
    #songtitle_eng = models.CharField(max_length=100)

    # for calculating MCMC ..?
    calclevel_easy = models.FloatField(default=0)
    calcweight_easy = models.FloatField(default=0)
    calclevel_normal = models.FloatField(default=0)
    calcweight_normal = models.FloatField(default=0)
    calclevel_hd = models.FloatField(default=0)
    calcweight_hd = models.FloatField(default=0)
    calclevel_exh = models.FloatField(default=0)
    calcweight_exh = models.FloatField(default=0)

    tag = models.CharField(default="", max_length=100, blank=True)

    def __unicode__(self):
        return self.songtitle + "/" + str(self.songlevel) + "/" + self.songtype

    def get_tags(self):
        if (self.tag == ""):
            return []
        else:
            return self.tag.split(",")

    class Meta:
        unique_together = ['songid', 'songtype',]

class Player(models.Model):
    """
    not log-in-available user. only for score retaining.
    also can relate with logged-in user.
    """
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=CASCADE)

    iidxid = models.CharField(max_length=20)
    iidxmeid = models.CharField(max_length=20)
    iidxnick = models.CharField(max_length=20)
    sppoint = models.IntegerField(default=0)
    dppoint = models.IntegerField(default=0)
    spclass = models.IntegerField(default=0)
    dpclass = models.IntegerField(default=0)

    private = models.BooleanField(default=False)

    # 프로필 사진. 비어 있으면 기본 이미지를 쓴다.
    avatar = models.ImageField(upload_to=avatar_upload_to, null=True, blank=True)

    splevel = models.FloatField(default=0)  # need to calculate
    dplevel = models.FloatField(default=0)  # need to calculate

    def __unicode__(self):
        return self.iidxnick + "/" + str(self.spclass) + "/" + str(self.dpclass)

    def iidxmeid_private(self):
        return self.iidxmeid[:1] + "*"*(len(self.iidxmeid)-2) + self.iidxmeid[-1:]
    def iidxnick_private(self):
        return self.iidxnick[:1] + "*"*(len(self.iidxnick)-2) + self.iidxnick[-1:]
    def isRefreshable(self):
        #print (now() - self.time).total_seconds() / 60 / 60 / 24
        return ((now() - self.time).total_seconds() / 60 / 60 / 24) >= 1
    def get_playrecord_count(self):
        return self.playrecord_set.count()

    def avatar_url(self):
        """템플릿에서 쓸 아바타 주소. 없으면 기본 이미지."""
        if self.avatar:
            try:
                return self.avatar.url
            except ValueError:
                pass
        return settings.STATIC_URL + 'qpro/infinitas.png'

class PlayRecord(models.Model):
    # MUST use db_index for performance
    player = models.ForeignKey(Player, db_index=True, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, db_index=True, on_delete=models.CASCADE)
    playscore = models.IntegerField(default=0)
    playclear = models.IntegerField(default=0)
    #playrank = models.IntegerField(default=0)
    playmiss = models.IntegerField(default=0, null=True)


class RankTable(models.Model):
    time = models.DateTimeField(default=now)        # db updated time
    tablename = models.CharField(max_length=100)
    tabletitle = models.CharField(max_length=100)
    tabletitlehtml = models.CharField(max_length=200)
    level = models.IntegerField(default=0)
    type = models.CharField(max_length=100)
    copyright = models.CharField(max_length=100)
    hit_count = GenericRelation(HitCount, object_id_field='object_pk',
        related_query_name='hit_count_generic_relation')

    def getTitleHTML(self):
        if (self.tabletitlehtml == ""):
            return self.tabletitle
        else:
            return self.tabletitlehtml

    def __unicode__(self):
        return self.tabletitle

class RankCategory(models.Model):
    ranktable = models.ForeignKey(RankTable, on_delete=models.CASCADE)
    categoryname = models.CharField(max_length=20)
    categorytype = models.IntegerField(default=0)
    sortindex = models.FloatField(default=None, null=True, blank=True)

    def get_sortindex(self):
        if (self.sortindex):
            return self.sortindex
        else:
            import re
            decimal = re.sub(r'[^0-9.]+', '', self.categoryname)
            if (decimal == ""):
                decimal = "0"
            return float(decimal)
    def get_tabletitle(obj):
        return obj.ranktable.tabletitle

    def __unicode__(self):
        return self.get_tabletitle() + "/" + self.categoryname

# CLAIM: this does same work as board category!
class RankItem(models.Model):
    rankcategory = models.ForeignKey(RankCategory, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, null=True, blank=True, on_delete=models.CASCADE)   # this cannot be null & can direct same song
    info = models.CharField(max_length=400)     # unique string, maybe...

    def get_songtitle(obj):
        return obj.song.songtitle
    def get_songlevel(obj):
        return obj.song.songlevel
    def get_ranktablename(obj):
        return obj.rankcategory.ranktable.tablename
    def get_categoryname(obj):
        return obj.rankcategory.categoryname

class MachineStatus(models.Model):
    machine_id = models.CharField(max_length=50, unique=True) # 예: 'hwajeong_iidx_1'
    waiting_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.machine_id}: {self.waiting_count} waiting"



class HealthCheck(models.Model):
    """상태 점검 한 번의 결과.

    업타임을 시계열로 보여 주려면 과거가 남아 있어야 한다. 요청이 올 때마다
    외부에 붙어 보는 것은 느리고 상대에게도 실례라, 주기적으로 돌린 결과를
    쌓아 두고 화면은 그것만 읽는다(iidxrank/management/commands/healthcheck.py).

    행이 무한정 늘지 않도록 그 명령이 오래된 것을 지운다.
    """

    OK = 'ok'
    DEGRADED = 'degraded'
    DOWN = 'down'
    STATUS_CHOICES = [(OK, 'ok'), (DEGRADED, 'degraded'), (DOWN, 'down')]

    target = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    latency_ms = models.IntegerField(default=0)
    note = models.CharField(max_length=200, blank=True, default='')
    checked_at = models.DateTimeField(db_index=True)

    class Meta:
        # 화면은 "대상별로 최근 것부터"만 읽는다. 그 순서로 색인을 둔다.
        index_together = [('target', 'checked_at')]
        ordering = ['-checked_at']

    def __str__(self):
        return '%s %s @%s' % (self.target, self.status, self.checked_at)

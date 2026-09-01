# dev/ — 개발·검증 도구

라이브 이미지에는 들어가지 않는다(`.dockerignore` 가 제외한다). 여기 있는 것은
전부 **개발용**이고, 저장소에 두는 이유는 하나다 — 세션이 끝나도 재현할 수 있어야
하기 때문이다.

```
dev/
├── docker-compose.yml   dev MySQL 8.0.46 (호스트 3307)
├── settings_dev.py      settings.py 를 import 한 뒤 dev MySQL 로 덮어쓴다
├── dbtool.py            덤프 적재 / 초기화
├── ranktable_drift.py   시트-DB 를 일부러 어긋나게 만든다 (확인 프롬프트 재현용)
├── fixtures/            구글 시트 HTML 스냅샷
├── checks/              회귀 검사
└── i18n/                번역 카탈로그 빌드
```

---

## dev MySQL 띄우기

```powershell
cd dev
docker compose up -d          # 컨테이너 bmapp-dev-mysql, 호스트 3307
```

데이터가 날아갔으면 저장소 밖의 덤프로 다시 올린다 (`dbtool.py` 참조).
dev DB 에는 **라이브 데이터가 익명화 없이** 들어 있다.

## dev 서버

```powershell
$py = "C:\Users\Vegarian\anaconda3\envs\bmapp39\python.exe"
& $py manage.py runserver 0.0.0.0:8731 --noreload --settings=dev.settings_dev
```

`--noreload` 다. **코드를 고쳤으면 죽이고 다시 띄운다.**

---

## checks/ — 회귀 검사

저장소 루트에서 돌린다. `_bootstrap.py` 가 `sys.path` 와
`DJANGO_SETTINGS_MODULE=dev.settings_dev` 를 맞춰 주므로 환경변수를 따로
설정할 필요는 없다(이미 설정돼 있으면 그것을 존중한다).

```powershell
& $py dev\checks\run_all.py          # 넷을 한꺼번에. 실패하면 exit 1
```

| 스크립트 | 무엇을 보나 | 기대값 |
|---|---|---|
| `compilecheck.py <루트>` | 전 `.py` 를 `py_compile` | FAIL 0 |
| `livecheck.py` | 주요 화면 12종의 상태·응답시간·쿼리 수, 콜레이션 | 실패 0 / 총 12 |
| `test_urls.py` | 새 주소, 옛 주소 301, 비공개 프로필, 가입 폼 문구 | 총 실패 0 |
| `untranslated.py` | 번역이 빠진 한국어 원문 | 0개 |

`livecheck.py` 와 `test_urls.py` 는 **dev MySQL 이 떠 있어야** 돈다.
`run_all.py` 는 `compilecheck` 의 OK 개수는 보지 않는다 — 파일이 늘면 같이 늘기
때문에 FAIL 만 본다.

의존성 조사용 두 개는 회귀 검사가 아니라 `requirements.txt` 를 다시 산출할 때만 쓴다.

| `deps.py` | AST 로 코드가 실제 import 하는 서드파티 최상위 모듈을 뽑는다 |
| `closure.py` | 그 직접 의존성에서 `requires` 를 따라 폐포를 구한다 |

> `closure.py` 의 `DIRECT` 목록은 손으로 유지한다. `Pillow` 는 Django 의
> 조건부 의존성이라 폐포에 안 잡혀 `requirements.txt` 에 따로 넣었다.

## i18n/ — 번역

이 PC 에 GNU gettext 가 없어 `msgfmt` 를 못 쓴다. `buildpo.py` 가 `.mo` 를
직접 쓴다.

```powershell
& $py dev\i18n\buildpo.py            # .po 병합 + .mo 재작성
```

새 문구를 추가하는 절차.

1. `{% trans %}` / `{% blocktrans %}` / `_()` 로 감싼다
2. `dev\checks\untranslated.py` 로 빠진 것을 찾는다
3. `dev/i18n/trans/newtrans_batchN.py` 를 새로 만들고 `buildpo.py` 의
   import 와 `NEW.update(...)` 에 연결한다
4. `buildpo.py` 실행
5. **서버를 재시작한다.** gettext 카탈로그는 프로세스 시작 때 한 번만 읽는다

> `blocktrans` 의 msgid 는 `{{ var }}` 가 아니라 **`%(var)s`** 다.
> 전에 이걸 빠뜨려 68개를 헛되이 넣은 적이 있다.

`buildpo.py` 는 import 만으로는 아무것도 쓰지 않는다(`build()` 는
`__main__` 에서만 돈다). `untranslated.py` 가 `read_po` 를 쓰려고 이 모듈을
import 하는데, 그때 카탈로그가 덮여 쓰이면 검사가 파일을 바꾸는 셈이 된다.

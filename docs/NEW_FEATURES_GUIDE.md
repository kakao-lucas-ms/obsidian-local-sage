# Obsidian Integration - New Features Guide

## 🎉 Overview

이 문서는 새로 추가된 고급 기능들을 설명합니다. 모든 기능은 Obsidian 내에서 Command Palette를 통해 사용하거나 CLI에서 직접 실행할 수 있습니다.

---

## 🔗 AI-Powered Link Suggestions (링크 제안)

### 기능
현재 문서와 의미론적으로 관련된 다른 문서들을 찾아 링크를 제안합니다.

### 사용법

**Obsidian에서:**
1. 링크를 추가하고 싶은 문서를 엽니다
2. Command Palette (Cmd+P)
3. "🔗 링크 제안" 실행
4. 결과 modal에서 제안된 wikilink를 복사
5. 문서에 붙여넣기

**CLI에서:**
```bash
python3 scripts/obsidian-suggest-links.py "path/to/note.md"
```

### 작동 방식
1. 문서의 핵심 구절 추출 (제목, 첫 문단, 주요 헤딩)
2. BGE-M3 embedding으로 벡터화
3. Qdrant에서 유사한 문서 검색
4. 점수 순으로 정렬하여 상위 8개 제안

### 출력 예시
```
🔗 링크 제안: 프로젝트 회고

🔍 관련 문서를 찾고 있습니다...

✅ 9개의 관련 문서를 찾았습니다!

1. 워크샵_프로세스_재사용_정리방법
   점수: 0.553
   링크: [[아이데이션 워크샵/워크샵_프로세스_재사용_정리방법|워크샵_프로세스_재사용_정리방법]]
   내용: 워크샵 프로세스를 정리하고 재사용하는 방법...

💡 위 링크를 복사해서 문서에 추가하세요
```

---

## 📊 Document Comparison (문서 비교)

### 기능
두 문서를 비교하여 유사점과 차이점을 분석합니다.

### 사용법

**CLI 전용:**
```bash
python3 scripts/obsidian-compare-docs.py "doc1.md" "doc2.md"
```

### 분석 항목
1. **기본 정보**: 단어 수, 줄 수, 헤딩, 태그, 링크
2. **의미론적 유사도**: Cosine similarity (0-1)
3. **텍스트 일치율**: 실제 내용 비교
4. **공통 요소**: 태그, 링크, 키워드
5. **고유 키워드**: 각 문서만의 특징
6. **제안사항**: 병합, 링크, 재구성 등

### 출력 예시
```
📊 문서 비교 분석
============================================================

📄 문서 1: 프로젝트 A 회고
   단어: 850, 줄: 120
   헤딩: 5, 태그: 3, 링크: 7

📄 문서 2: 프로젝트 B 회고
   단어: 920, 줄: 135
   헤딩: 6, 태그: 4, 링크: 5

============================================================

🔍 의미론적 유사도 분석 중...
   유사도: 0.750 (75%)
   ✅ 매우 유사한 문서입니다

📝 내용 비교...
   텍스트 일치율: 35%
   공통 줄: 42/135

💡 제안:
• 문서가 매우 유사합니다. 하나로 합치는 것을 고려하세요
```

---

## 📦 Batch Processing (배치 처리)

### 기능
여러 문서를 한 번에 처리합니다.

### 사용법

**CLI 전용:**

#### 1. 폴더 요약
```bash
python3 scripts/obsidian-batch-process.py summary "folder/path"
```

폴더 내 문서 통계:
- 총 문서 수
- 파일 유형별 개수
- 총 크기
- 문서 목록 (최대 20개)

#### 2. MOC (Map of Content) 생성
```bash
python3 scripts/obsidian-batch-process.py moc "folder/path" --title "프로젝트 목차"
```

폴더 내 모든 문서의 목차를 생성:
- 폴더별 그룹화
- Wikilink 형식
- 날짜/시간 자동 기록

출력을 새 노트로 저장하여 사용:
```bash
python3 scripts/obsidian-batch-process.py moc "Projects/" > "Projects/README.md"
```

#### 3. 태그 일괄 추가
```bash
python3 scripts/obsidian-batch-process.py add-tag "folder/path" --tag "프로젝트"
```

폴더 내 모든 문서에 태그 추가:
- 기존 태그 중복 체크
- Frontmatter 또는 제목 다음에 삽입
- 진행 상황 표시

#### 4. 깨진 링크 검사
```bash
python3 scripts/obsidian-batch-process.py check-links "folder/path"
```

폴더 내 모든 깨진 링크 찾기:
- Wikilink 대상 파일 존재 확인
- 문서별 깨진 링크 목록
- 통계 정보

#### 5. 재귀 처리
```bash
python3 scripts/obsidian-batch-process.py summary "folder/" --recursive
```

`--recursive` 또는 `-r` 옵션으로 하위 폴더 포함

#### 6. 태그 기반 선택
```bash
python3 scripts/obsidian-batch-process.py summary "#프로젝트"
```

특정 태그를 가진 모든 문서 처리

### 출력 예시

**폴더 요약:**
```
📊 폴더 요약
============================================================

총 문서: 45개

📄 파일 유형:
   .md: 45개

💾 총 크기: 287.3 KB

📝 문서 목록:
   1. 프로젝트 A
   2. 프로젝트 B
   ...
```

**MOC 생성:**
```markdown
# 프로젝트 목차

생성일: 2026-01-21 01:30
문서 수: 45개

---

## 2025

- [[Projects/2025/프로젝트 A|프로젝트 A]]
- [[Projects/2025/프로젝트 B|프로젝트 B]]

## 2026

- [[Projects/2026/신규 프로젝트|신규 프로젝트]]
```

---

## 🏥 Vault Health Check (건강 체크)

### 기능
Vault 전체를 스캔하여 다양한 문제를 찾습니다.

### 사용법

**Obsidian에서:**
1. Command Palette (Cmd+P)
2. "🏥 Vault 건강 체크" 실행
3. 결과 modal 확인

**CLI에서:**
```bash
python3 scripts/obsidian-health-check.py
```

### 검사 항목

1. **📄 빈 문서**
   - 내용이 전혀 없는 문서
   - 거의 빈 문서 (< 20자)

2. **🔗 고립된 문서**
   - 다른 문서에서 링크되지 않은 문서
   - Index/MOC 제외

3. **🔗 깨진 링크**
   - 존재하지 않는 문서를 가리키는 wikilink

4. **📁 중복 이름**
   - 다른 폴더에 같은 이름의 문서

5. **⏰ 오래된 문서**
   - 1년 이상 수정되지 않은 문서

6. **📏 큰 문서**
   - 100KB 이상의 문서
   - 분리 고려 필요

7. **🏷️ 태그 없는 문서**
   - 태그가 하나도 없는 문서

8. **✅ 미완료 TODO**
   - `- [ ]` 형식의 체크박스
   - 문서별 개수

### 출력 예시
```
🏥 Obsidian Vault Health Check
============================================================

📁 문서 검색 중...
   발견: 1769개 문서

📄 빈 문서 검사...
🔗 고립된 문서 검사...
🔗 깨진 링크 검사...
📁 중복 이름 검사...
⏰ 오래된 문서 검사...
📏 큰 문서 검사...
🏷️  태그 없는 문서 검사...
✅ TODO 항목 검사...

============================================================
📊 Vault Health Check Report
============================================================

📄 빈 문서: 8개
   • 무제.md
   • 2026-01-13.md
   ... +6개 더

🔗 고립된 문서 (링크 없음): 1766개
   • ㅇㅇㄹㅁㄴㅇㄹ.md
   • 테크리더 위클리에 공유 할만한거.md
   ... +1764개 더

🔗 깨진 링크: 88개
   • 1.md → [[톡터디 발표.md]]
   ... +87개 더

============================================================
총 문제: 1932개

💡 제안:
• 빈 문서는 내용을 추가하거나 삭제하세요
• 고립된 문서는 다른 문서에서 링크하세요
• 깨진 링크는 수정하거나 제거하세요
```

---

## 🎯 Use Cases (활용 사례)

### 1. 프로젝트 문서 정리

```bash
# 프로젝트 폴더 건강 체크
python3 scripts/obsidian-batch-process.py check-links "Projects/MyProject/"

# MOC 생성
python3 scripts/obsidian-batch-process.py moc "Projects/MyProject/" \
    --title "MyProject 목차" > "Projects/MyProject/README.md"

# 모든 문서에 태그 추가
python3 scripts/obsidian-batch-process.py add-tag "Projects/MyProject/" \
    --tag "프로젝트2025"
```

### 2. 회고 문서 연결

```bash
# 비슷한 회고 찾기
python3 scripts/obsidian-suggest-links.py "Retrospectives/2026-Q1.md"

# 두 분기 회고 비교
python3 scripts/obsidian-compare-docs.py \
    "Retrospectives/2025-Q4.md" \
    "Retrospectives/2026-Q1.md"
```

### 3. 주간 Vault 관리

```bash
# 전체 건강 체크
python3 scripts/obsidian-health-check.py

# 빈 문서 정리
# (출력을 보고 수동으로 처리)

# 오래된 문서에 archive 태그 추가
python3 scripts/obsidian-batch-process.py add-tag "OldNotes/" --tag "archive"
```

### 4. 학습 노트 정리

```bash
# 학습 주제별 폴더 요약
python3 scripts/obsidian-batch-process.py summary "Learning/JavaScript/" -r

# MOC 생성
python3 scripts/obsidian-batch-process.py moc "Learning/JavaScript/" \
    --title "JavaScript 학습 노트" > "Learning/JavaScript/INDEX.md"

# 관련 노트 링크
# 각 노트에서 Obsidian Command: "🔗 링크 제안" 실행
```

---

## 🔧 Advanced Configuration

### CLI 도구 위치
```
scripts/
├── obsidian-suggest-links.py       # 링크 제안
├── obsidian-suggest-links-wrapper.sh
├── obsidian-compare-docs.py        # 문서 비교
├── obsidian-batch-process.py       # 배치 처리
└── obsidian-health-check.py        # 건강 체크
```

### 의존성
- **Python 3**: 모든 스크립트
- **Ollama**: BGE-M3 embedding (링크 제안, 문서 비교)
- **Qdrant**: 벡터 검색 (링크 제안)
- **SQLite**: 문서 인덱스 (링크 제안, 배치 처리)

### 커스터마이징

**검색 결과 개수 조정** (링크 제안):
```python
# scripts/obsidian-suggest-links.py:50
results = find_similar_documents(file_path, limit=10)  # 기본 10개
```

**유사도 임계값 조정** (문서 비교):
```python
# scripts/obsidian-compare-docs.py:100
if similarity > 0.8:  # 매우 유사
elif similarity > 0.6:  # 유사
elif similarity > 0.4:  # 일부 관련
```

**오래된 문서 기준 변경** (건강 체크):
```python
# scripts/obsidian-health-check.py:82
threshold = datetime.now() - timedelta(days=365)  # 기본 1년
```

---

## 📝 Tips & Best Practices

### 링크 제안
- 새 문서 작성 후 바로 실행하여 관련 문서 연결
- 주기적으로 실행하여 연결 누락 방지
- 점수가 0.5 이상인 경우 매우 관련성 높음

### 문서 비교
- 유사도 > 0.7: 병합 고려
- 유사도 0.4-0.7: 상호 참조 링크 추가
- 유사도 < 0.4: MOC로 연결

### 배치 처리
- 큰 작업 전에는 백업 필수
- `--recursive`는 신중히 사용 (하위 폴더 많으면 느림)
- MOC는 정기적으로 재생성하여 최신 상태 유지

### 건강 체크
- 주 1회 정기 실행 권장
- 고립된 문서는 정상일 수 있음 (일기, 임시 노트 등)
- 깨진 링크 우선 수정
- 빈 문서는 바로 삭제 또는 내용 추가

---

## 🐛 Troubleshooting

### 오류: "Cannot connect to Ollama"
```bash
# Ollama 실행 확인
ollama list

# 모델 다운로드
ollama pull bge-m3
```

### 오류: "Cannot connect to Qdrant"
```bash
# Qdrant 실행 확인
curl http://127.0.0.1:6333/collections
```

### 오류: "Database not found"
```bash
# 인덱스 재구축
bash scripts/fix-all-issues.sh
```

### 느린 실행 속도
- Vault 크기가 클 경우 정상
- 필요한 폴더만 지정하여 처리
- 백그라운드에서 실행 고려

---

## 📚 Related Documentation

- [OBSIDIAN_INTEGRATION_STATUS.md](./OBSIDIAN_INTEGRATION_STATUS.md) - 기본 기능 상태
- [README.md](./README.md) - 전체 프로젝트 개요
- [workflows/README.md](./workflows/README.md) - 워크플로우 문서

---

## 🎯 Summary

### Obsidian Commands (Command Palette)
1. 🔗 링크 제안 - AI 기반 관련 문서 찾기
2. 🏥 Vault 건강 체크 - 전체 문제 스캔

### CLI Tools
1. `obsidian-compare-docs.py` - 두 문서 상세 비교
2. `obsidian-batch-process.py` - 배치 작업
   - `summary` - 폴더 통계
   - `moc` - 목차 생성
   - `add-tag` - 태그 추가
   - `check-links` - 링크 검사

모든 도구는 한글 파일명과 경로를 완벽 지원합니다!

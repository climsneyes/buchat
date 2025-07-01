# 해시 기반 캐싱 시스템

이 프로젝트는 PDF 파일의 해시값을 기반으로 임베딩을 캐싱하여, 파일이 변경되지 않았을 때는 추가적인 임베딩 생성 없이 기존 벡터DB를 재사용할 수 있도록 합니다.

## 주요 기능

### 1. 파일 해시 기반 캐싱
- PDF 파일의 MD5 해시를 계산하여 파일 변경사항을 감지
- 파일이 변경되지 않았으면 기존 벡터DB를 즉시 로드
- 파일이 변경되었으면 자동으로 새로운 임베딩 생성

### 2. 캐시 정보 관리
- `chroma_db/cache_info.json` 파일에 캐시 메타데이터 저장
- 파일 해시, 청크 수, 생성 시간 등 정보 포함

### 3. 캐시 관리 도구
- 캐시 상태 확인
- 강제 캐시 재생성
- 캐시 완전 삭제

## 사용법

### 기본 사용법

```python
from rag_utils import get_or_create_vector_db

# API 키 설정
api_key = "your-openai-api-key"

# 벡터DB 가져오기 (캐시 자동 처리)
vector_db = get_or_create_vector_db(api_key)
```

### 캐시 관리 스크립트 사용

```bash
# 캐시 상태 확인
python cache_manager.py status

# 캐시 강제 재생성
python cache_manager.py rebuild

# 캐시 완전 삭제
python cache_manager.py clear
```

## 캐시 상태 확인

캐시 상태는 다음과 같은 정보를 제공합니다:

- **상태**: `valid`, `invalid`, `not_exists`, `no_cache_info`, `error`
- **현재 파일 해시**: 현재 PDF 파일의 MD5 해시 (앞 8자리)
- **캐시된 파일 해시**: 저장된 PDF 파일의 MD5 해시 (앞 8자리)
- **청크 수**: PDF에서 생성된 텍스트 청크의 개수
- **생성 시간**: 캐시가 생성된 시간

## 동작 방식

### 1. 첫 실행 시
1. PDF 파일의 MD5 해시 계산
2. PDF를 청크로 분할
3. OpenAI 임베딩 생성
4. Chroma 벡터DB에 저장
5. 캐시 정보 (`cache_info.json`) 저장

### 2. 재실행 시
1. 현재 PDF 파일의 MD5 해시 계산
2. 저장된 캐시 정보와 해시 비교
3. **해시가 동일하면**: 기존 벡터DB 즉시 로드
4. **해시가 다르면**: 기존 벡터DB 삭제 후 새로 생성

## 파일 구조

```
project/
├── pdf/
│   └── ban.pdf                    # 원본 PDF 파일
├── chroma_db/
│   ├── cache_info.json           # 캐시 메타데이터
│   ├── chroma.sqlite3           # Chroma 벡터DB
│   └── [collection_files]       # Chroma 컬렉션 파일들
├── rag_utils.py                 # 메인 RAG 유틸리티
└── cache_manager.py             # 캐시 관리 스크립트
```

## 장점

1. **성능 향상**: 파일이 변경되지 않았을 때 임베딩 생성 시간 절약
2. **비용 절약**: OpenAI API 호출 횟수 감소
3. **자동 관리**: 파일 변경 시 자동으로 캐시 무효화 및 재생성
4. **투명성**: 캐시 상태를 명확하게 확인 가능

## 주의사항

- PDF 파일이 변경되면 자동으로 새로운 임베딩이 생성됩니다
- 캐시를 강제로 재생성하려면 `cache_manager.py rebuild` 명령을 사용하세요
- 캐시를 완전히 삭제하려면 `cache_manager.py clear` 명령을 사용하세요

## 예제 출력

### 캐시 상태 확인
```
=== 캐시 상태 확인 ===
PDF 파일 경로: pdf/ban.pdf
벡터DB 경로: chroma_db
상태: valid
메시지: 캐시가 유효합니다. (파일 해시: a1b2c3d4...)
현재 파일 해시: a1b2c3d4...
캐시된 파일 해시: a1b2c3d4...
청크 수: 45
생성 시간: 1703123456.789
유효성: ✅ 유효
```

### 파일 변경 시
```
PDF 파일이 변경되었습니다. (이전 해시: a1b2c3d4..., 현재 해시: e5f6g7h8...)
캐시가 유효하지 않아 새로운 임베딩을 생성합니다...
기존 벡터DB를 삭제했습니다.
PDF 청크 개수: 45
새로운 Chroma DB 생성 및 저장 완료 (청크 수: 45)
파일 해시: e5f6g7h8...
``` 
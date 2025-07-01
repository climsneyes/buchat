# 베이스 이미지
FROM python:3.12-slim

# 작업 디렉토리 생성 및 이동
WORKDIR /app

# 필수 파일 복사
COPY requirements.txt ./
COPY . .

# 의존성 설치
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 포트 설정 (필요시)
EXPOSE 8000

# 실행 명령 (main.py가 진입점)
CMD ["python", "main.py"] 
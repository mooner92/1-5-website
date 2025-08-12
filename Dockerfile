# 파이썬 3.9 버전을 베이스 이미지로 사용
FROM python:3.9-slim

# 작업 디렉터리를 /app으로 설정
WORKDIR /app

# 현재 디렉터리의 모든 파일을 /app으로 복사
COPY . /app

# 필요한 파이썬 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 컨테이너가 5000번 포트를 외부에 노출
EXPOSE 5000

# 환경 변수 설정
ENV FLASK_APP=my-website/flask_app.py
ENV FLASK_ENV=production

# Flask 앱 실행
CMD ["python", "my-website/flask_app.py"]
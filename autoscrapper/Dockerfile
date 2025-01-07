FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

RUN playwright install chromium
RUN playwright install-deps

CMD ["uvicorn", "core.server.api_routes:app", "--loop", "asyncio", "--host", "0.0.0.0", "--port", "8000"]

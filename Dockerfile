FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apk_builder ./apk_builder
EXPOSE 8789
CMD ["uvicorn", "apk_builder.app:APP", "--host", "0.0.0.0", "--port", "8789"]

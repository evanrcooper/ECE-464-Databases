FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get upgrade -y

COPY ./WebApp/ /app/

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD ["python3", "/app/WebApp/main.py"]
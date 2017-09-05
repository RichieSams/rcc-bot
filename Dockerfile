FROM alpine:3.6

RUN apk add --no-cache ca-certificates

RUN apk add --no-cache \
	openssl \
	python3 \
	
	&& easy_install-3.6 pip \
	&& pip install --upgrade pip

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY main.py /app/main.py
	
RUN pip install -r requirements.txt

CMD ["python3", "main.py"]

FROM python:3.9-slim
LABEL maintainer="PeanutMelonSeedBigAlmond"
ENV TZ="Asia/Shanghai"
ENV CONTAINER_MODE="1"
WORKDIR /app
COPY . .
VOLUME [ "/config" ]
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
ENTRYPOINT [ "python", "main.py" ]
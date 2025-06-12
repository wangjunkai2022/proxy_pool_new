FROM python:3.13-alpine

LABEL maintainer="jinting <yueluo368@gmail.com>"

WORKDIR /proxy-pool-new

COPY ./requirements.txt .

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
    apk add -U --no-cache tzdata musl-dev gcc libxml2-dev libxslt-dev && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev tzdata

COPY . .

RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

VOLUME ["/proxy-pool-new"]

EXPOSE 5010

ENTRYPOINT [ "sh", "start.sh" ]
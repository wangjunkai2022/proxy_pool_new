FROM python:3.12-alpine

LABEL maintainer="jinting <yueluo368@gmail.com>"

# 1. 创建并切到工作目录
RUN mkdir -p /proxy-pool-new
WORKDIR /proxy-pool-new

# 2. 拷贝依赖清单，并安装依赖
COPY ./requirements.txt .

# apk repository
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories

# timezone
RUN apk add -U tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && apk del tzdata

# runtime environment
RUN apk add musl-dev gcc libxml2-dev libxslt-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev

# 3. 拷贝剩余所有文件
COPY . .

# 4. 如果有 CRLF 问题，用 sed 去掉 Windows 回车
RUN sed -i 's/\r$//' start.sh \
    && chmod +x start.sh

VOLUME ["/proxy-pool-new"]

EXPOSE 5010

ENTRYPOINT [ "sh", "start.sh" ]

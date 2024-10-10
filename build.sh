#!/bin/bash

# 檢查是否已經存在舊的 Docker 映像
IMAGE_NAME="netviz:latest"
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" != "" ]]; then
    echo "移除舊的 Docker 映像..."
    docker rmi -f $IMAGE_NAME
fi

# 建立新的 Docker 映像
echo "建立新的 Docker 映像..."
docker build -t $IMAGE_NAME .

echo "建立完成: $IMAGE_NAME"

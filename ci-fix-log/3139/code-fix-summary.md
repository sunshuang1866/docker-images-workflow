# 修复摘要

## 修复的问题
CI 构建失败为基础设施问题（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败的直接原因是 `pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/` 在下载 `nvidia-cudnn-cu13`（366 MB）时发生 `ReadTimeoutError`，属于阿里云镜像站的 TCP 读超时。该 Dockerfile 语法正确、依赖声明正确，失败与 PR 代码逻辑无关，属于外部镜像站的瞬态网络不稳定问题。同样配置在其他时间或使用其他镜像源重试很可能成功。

## 潜在风险
无
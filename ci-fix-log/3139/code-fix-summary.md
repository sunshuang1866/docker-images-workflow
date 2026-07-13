# 修复摘要

## 修复的问题
CI 构建过程中从 `mirrors.aliyun.com` 下载大型 Python 包 `nvidia-cudnn-cu13`（366 MB）时发生 TCP 读取超时，属于基础设施层面的网络瞬态故障（`infra-error`），与 PR 代码逻辑无关，无需修改代码。

## 修改的文件
无（基础设施错误，无需代码修改）

## 修复逻辑
本次失败为 CI 构建节点到阿里云镜像站的网络连接在下载大文件时发生超时，属于瞬态基础设施问题。`Dockerfile` 中使用 `-i https://mirrors.aliyun.com/pypi/simple/` 作为 pip 索引源本身没有问题，重试 CI 构建有较大概率成功。若多次重试均在同一包下载超时，可考虑换用其他 PyPI 镜像源（如默认 PyPI 源或华为云镜像 `mirrors.huaweicloud.com`）。

## 潜在风险
无
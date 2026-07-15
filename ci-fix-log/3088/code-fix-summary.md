# 修复摘要

## 修复的问题
Docker 构建时 wget 下载 `dlcdn.apache.org` 上 Druid 35.0.0 制品返回 HTTP 404，将下载源更换为 `archive.apache.org` 以支持历史版本。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 wget 下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/druid/`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 仅保留最新版本制品，Druid 35.0.0 已非最新版本，其制品在 CDN 上已下架，导致 wget 返回 404。`archive.apache.org` 保留所有历史版本制品，适用于固定版本的 Docker 构建。经验证，新 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200。

## 潜在风险
`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile` 仍使用 `dlcdn.apache.org` 作为下载源，可能在未来构建时出现相同问题。但该文件不在本次 PR 变更范围内，未做修改。
# 修复摘要

## 修复的问题
Dockerfile 中 `git clone --depth 1` 浅克隆无法 checkout 历史 commit hash `3b0ff80`，导致构建失败。

## 修改的文件
- `AI/xla/3b0ff80/24.03-lts-sp3/Dockerfile`: 将 git 操作从 `git clone --depth 1 ... && git checkout ${VERSION}` 改为 `git init . && git remote add origin ... && git fetch --depth 1 origin ${VERSION} && git checkout FETCH_HEAD`

## 修复逻辑
`git clone --depth 1` 只拉取默认分支最新 commit，随后 `git checkout ${VERSION}` 无法定位到 commit `3b0ff80`（它是历史 commit，不在浅克隆范围内）。修复方案改用 `git fetch --depth 1 origin <sha>` 直接按 commit hash 拉取，通过 `git checkout FETCH_HEAD` 检出目标 commit。已从上游 `openxla/xla` 仓库确认 commit `3b0ff80` 存在且可访问。

## 潜在风险
无
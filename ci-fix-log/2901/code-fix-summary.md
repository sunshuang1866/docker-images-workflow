# 修复摘要

## 修复的问题
Dockerfile 引用的辅助文件 `entrypoint.sh` 和 `tap2json.py` 未随 PR 提交到 `24.03-lts-sp4` 目录，导致 BuildKit 无法计算文件校验和，构建失败。

## 修改的文件
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/entrypoint.sh`: 从 `22.03-lts-sp4` 目录复制，内容完全一致
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/tap2json.py`: 从 `22.03-lts-sp4` 目录复制，内容完全一致

## 修复逻辑
Dockerfile 第 99 行 `COPY entrypoint.sh tap2json.py /` 需要构建上下文中有这两个文件。已有的 `22.03-lts-sp4` 版本目录中存在同名文件，且两个版本的 Dockerfile 除 `ARG BASE` 行外完全一致，说明这两个辅助脚本在所有 kselftests-virtme 版本之间是通用的。直接复制到新版本目录即可解决构建失败。

## 潜在风险
无。这两个文件与 `22.03-lts-sp4` 版本中的完全一致，不影响其他版本或功能。
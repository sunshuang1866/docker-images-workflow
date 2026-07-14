# 修复摘要

## 修复的问题
Dockerfile 中 `COPY entrypoint.sh tap2json.py /` 引用的两个辅助脚本文件未随 PR 提交，导致 BuildKit 构建时找不到文件而失败。

## 修改的文件
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/entrypoint.sh`: 从 `22.03-lts-sp4` 同名目录复制，内容完全一致
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/tap2json.py`: 从 `22.03-lts-sp4` 同名目录复制，内容完全一致

## 修复逻辑
CI 分析报告指出，`24.03-lts-sp4` 版本的 Dockerfile（第 99 行 `COPY entrypoint.sh tap2json.py /`）引用了两个不存在于该目录的辅助脚本文件。这两个文件在已有的 `22.03-lts-sp4` 版本目录中存在，且它们在各 kselftests-virtme 版本间是通用的（内容完全相同）。将这两个文件直接复制到 `24.03-lts-sp4/` 目录即可满足 Dockerfile 的构建依赖。经比对，`22.03-lts-sp4` 和 `24.03-lts-sp4` 的 Dockerfile 除基础镜像 ARG 参数外完全一致，两个辅助脚本在所有版本间通用，因此直接复制即可。

## 潜在风险
无
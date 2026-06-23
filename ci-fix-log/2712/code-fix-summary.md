# 修复摘要

## 修复的问题
Dockerfile 中 `git fetch --depth 1 origin ${VERSION}` 使用了 7 字符缩写 Git SHA（`3b0ff80`），Git 无法将缩写 SHA 解析为远程 ref，导致 `fatal: couldn't find remote ref` 构建失败。

## 修改的文件
- `AI/xla/3b0ff80/24.03-lts-sp3/Dockerfile`: 将 `ARG VERSION=3b0ff80` 改为 `ARG VERSION=3b0ff804f29ee5bb224854bf0e12fc0cbecb6db9`（完整 40 字符 SHA）

## 修复逻辑
通过 GitHub API (`api.github.com/repos/openxla/xla/commits/3b0ff80`) 确认 commit `3b0ff80` 的完整 SHA 为 `3b0ff804f29ee5bb224854bf0e12fc0cbecb6db9`，commit 存在且可访问。Git 在 `fetch` 操作中要求远程 ref 必须是完整 SHA（40 字符）、分支名或标签名，缩写 SHA 无法被解析。将 `VERSION` 改为完整 SHA 后，`git fetch --depth 1 origin ${VERSION}` 将能正常执行。已从上游 master 获取该 commit 信息验证，完整 SHA 确认存在。

## 潜在风险
无。该修改仅将缩写 SHA 替换为其对应的完整 40 字符 SHA，指向完全相同的 commit，不改变拉取的源码内容。目录名、镜像 tag 名（如 `3b0ff80-oe2403sp3`）和其他文档中出现的 `3b0ff80` 是命名标识符而非 git 操作参数，不受影响，无需修改。
# 修复摘要

## 修复的问题
`git clone --depth 1` 浅克隆后无法 checkout 指定 commit hash，导致 3FS 镜像构建在错误源码上执行从而编译失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 第22-24行的 git clone/checkout/submodule update 命令，去掉 `--depth 1` 和错误掩码 `2>/dev/null || true`

## 修复逻辑
1. 去掉 `git clone --recurse-submodules --depth 1 --shallow-submodules` 中的 `--depth 1` 和 `--shallow-submodules`，改为完整克隆，确保 `ARG VERSION=22fca04` 对应的 commit 在本地仓库中可访问
2. 去掉 `git checkout ${VERSION} 2>/dev/null || true` 中的 `2>/dev/null || true`，使 checkout 失败时显式报错而非静默跳过
3. 去掉 `git submodule update --init --recursive --depth 1 2>/dev/null || true` 中的 `--depth 1`（与完整克隆保持一致）和 `2>/dev/null || true`，使 submodule 更新失败时显式报错

以上修改直接解决了 CI 分析报告中指出的根因：浅克隆后 commit hash checkout 不兼容 + 错误掩码掩盖构建失败。

## 潜在风险
- 去掉 `--depth 1` 后克隆体积和耗时增加，但对构建环境来说是可接受的
- 如果 commit `22fca04` 在 deepseek-ai/3fs 仓库中不存在或不完整（如已被 GC），即使完整克隆也无法 checkout，需要进一步确认该 commit 的有效性
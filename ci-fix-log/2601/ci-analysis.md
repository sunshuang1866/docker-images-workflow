# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: COPY脚本缺执行权限
- 新模式症状关键词: Permission denied, exit code: 126, COPY, chmod

## 根因分析

### 直接错误
```
#13 [7/7] RUN ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ "amd64" = "arm64" ]; then         BRANCH="main";     fi &&     ./build-Slicer.sh v5.10.0
#13 0.063 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#13 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ \"$TARGETARCH\" = \"arm64\" ]; then         BRANCH=\"main\";     fi &&     ./build-Slicer.sh ${BRANCH}" did not complete successfully: exit code: 126
------
Dockerfile:20
```

### 根因定位
- 失败位置: `Dockerfile:20` (RUN 行)
- 失败原因: Dockerfile 中通过 `COPY` 将 `build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh` 三个脚本复制到容器后，未执行 `chmod +x` 赋予执行权限，导致 `./build-CTKAppLauncher.sh` 直接运行时报 `Permission denied`，退出码 126。

### 与 PR 变更的关联
PR 新增了全部失败相关的文件（Dockerfile 及三个构建脚本）。Dockerfile 中 `COPY` 了三个 `.sh` 脚本文件但遗漏了 `RUN chmod +x` 步骤，直接导致本次构建失败。与 PR 改动直接相关。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `COPY` 脚本步骤之后、`RUN` 执行脚本之前，增加一行 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh` 为脚本赋予执行权限。

### 方向 2（可选）
若不希望增加额外的 `RUN` 层，也可在 COPY 之前的 `yum install` 步骤中追加 `RUN chmod +x`，或在 COPY 后合并为同一个 RUN 指令。但考虑到 Dockerfile 当前结构（COPY 和 RUN 已分层），方向 1 最简单直接。

## 需要进一步确认的点
- 无需进一步确认，根因明确。

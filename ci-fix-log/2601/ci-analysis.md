# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Shell脚本缺少执行权限
- 新模式症状关键词: Permission denied, exit code 126, ./build-CTKAppLauncher.sh, 100644

## 根因分析

### 直接错误
```
#14 [8/8] RUN ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ "amd64" = "arm64" ]; then         BRANCH="main";     fi &&     ./build-Slicer.sh v5.10.0 /opt/zlib.patch
#14 0.068 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#14 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh && ..." did not complete successfully: exit code: 126
------
Dockerfile:21
--------------------
  20 |     WORKDIR /opt/
  21 | >>> RUN ./build-CTKAppLauncher.sh && \
  22 | >>>     ./build-tbb.sh && \
  23 | >>>     if [ "$TARGETARCH" = "arm64" ]; then \
  24 | >>>         BRANCH="main"; \
  25 | >>>     fi && \
  26 | >>>     ./build-Slicer.sh ${BRANCH} /opt/zlib.patch
  27 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 126
```

### 根因定位
- 失败位置: Dockerfile:21
- 失败原因: 三个新增的 Shell 脚本（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）提交时文件模式为 `100644`（无执行权限），Docker 构建时无法直接执行 `./build-CTKAppLauncher.sh`，返回 exit code 126。

### 与 PR 变更的关联
PR 新增了 3 个 shell 脚本（通过 COPY 指令拷入镜像并在 RUN 中直接执行），但所有脚本的 git 文件模式均为 `100644`（缺少 execute 位）。Dockerfile 在 RUN 指令中直接以 `./build-CTKAppLauncher.sh` 方式调用，未通过 `bash` 显式解释执行，因此触发 `Permission denied`。失败直接由本次 PR 的变更引起。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中，于 COPY 之后、RUN 执行脚本之前，添加 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh`，赋予脚本可执行权限。

### 方向 2（置信度: 高）
在 Dockerfile 的 RUN 指令中改用 `bash ./build-CTKAppLauncher.sh` 方式调用，通过 `bash` 显式解释执行，绕过执行权限检查。

### 方向 3（置信度: 中）
确保在 git 仓库中将这三个脚本文件提交为可执行模式（`100755`），从根本上解决权限问题。但这依赖于仓库的工作流和文件提交机制是否支持。

## 需要进一步确认的点
- 无需进一步确认，日志证据完整且明确。

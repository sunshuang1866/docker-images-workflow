# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 脚本缺少执行权限
- 新模式症状关键词: Permission denied, COPY, shell script, exit code 126

## 根因分析

### 直接错误
```
#13 [7/7] RUN ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ "amd64" = "arm64" ]; then         BRANCH="main";     fi &&     ./build-Slicer.sh v5.10.0
#13 0.061 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#13 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ \"$TARGETARCH\" = \"arm64\" ]; then         BRANCH=\"main\";     fi &&     ./build-Slicer.sh ${BRANCH}" did not complete successfully: exit code: 126
------
> [7/7] RUN ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ "amd64" = "arm64" ]; then         BRANCH="main";     fi &&     ./build-Slicer.sh v5.10.0:
0.061 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
------
Dockerfile:20
--------------------
  19 |     WORKDIR /opt/
  20 | >>> RUN ./build-CTKAppLauncher.sh && \
  21 | >>>     ./build-tbb.sh && \
  22 | >>>     if [ "$TARGETARCH" = "arm64" ]; then \
  23 | >>>         BRANCH="main"; \
  24 | >>>     fi && \
  25 | >>>     ./build-Slicer.sh ${BRANCH}
  26 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 126
```

### 根因定位
- 失败位置: `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile:20`
- 失败原因: 通过 `COPY` 指令复制到镜像内的三个 shell 脚本（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）缺少可执行权限（`+x`），导致 `RUN` 指令中直接执行 `./build-CTKAppLauncher.sh` 时返回 `Permission denied`（exit code 126）。

### 与 PR 变更的关联
PR 新增了 4 个构建脚本文件（3 个 `.sh` + 1 个 `.patch`）和 1 个 Dockerfile。三个 `.sh` 文件均为新文件（`new_file: True`），提交到仓库时未设置可执行权限位。Docker 的 `COPY` 指令会保留源文件的权限元数据，因此脚本在容器内不可执行，最终在 `RUN` 步骤直接调用时报错。此失败**完全由本次 PR 改动引入**。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `RUN` 步骤中，执行脚本前先用 `chmod +x` 为三个脚本添加可执行权限。例如在 `WORKDIR /opt/` 之后、执行脚本之前添加 `RUN chmod +x ./build-CTKAppLauncher.sh ./build-tbb.sh ./build-Slicer.sh`。

### 方向 2（置信度: 高）
在提交到 Git 仓库前，通过 `git update-index --chmod=+x` 或直接在文件系统上 `chmod +x` 后提交，使脚本文件在仓库中即带有可执行权限位，这样 Docker `COPY` 时权限也会保留为可执行。

## 需要进一步确认的点
- 其他架构（arm64）的下游构建 job 是否也会遇到相同问题（日志仅展示了 x86_64/Docker build 阶段的失败，arm64 构建 job 日志未提供）。

# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 脚本无执行权限
- 新模式症状关键词: Permission denied, exit code: 126, COPY, chmod, .sh

## 根因分析

### 直接错误
```
#14 0.067 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#14 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ \"$TARGETARCH\" = \"arm64\" ]; then         BRANCH=\"main\";     fi &&     ./build-Slicer.sh ${BRANCH} /opt/zlib.patch" did not complete successfully: exit code: 126
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
- 失败位置: `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`:21
- 失败原因: Docker `COPY` 指令将 `build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh` 复制到 `/opt/` 后，文件缺少可执行权限（`chmod +x`），导致 Shell 直接运行 `./build-CTKAppLauncher.sh` 时报 "Permission denied"（exit code 126）

### 与 PR 变更的关联
**直接关联**。本 PR 新增了全部 5 个文件（Dockerfile + 3 个构建脚本 + 1 个 patch）。Dockerfile 在 `RUN` 步骤（第 21 行）中直接执行 `./build-CTKAppLauncher.sh`，但在此之前没有任何 `chmod +x` 操作来赋予脚本可执行权限。`COPY` 指令保留源文件的权限位，而仓库中新提交的 `.sh` 文件不具备可执行位。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中，`COPY` 三个 `.sh` 脚本之后、`RUN` 执行之前，添加一个 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh` 步骤，或在同一个 `RUN` 命令开头先执行 `chmod +x` 再运行脚本。

### 方向 2（置信度: 中）
在 Git 仓库中直接设置 `.sh` 文件的可执行位（`git update-index --chmod=+x` 或 `chmod +x` 后重新提交），使 `COPY` 进入镜像时自然带有执行权限。此方法更适合一次性设置，后续版本维护时不易遗漏。

## 需要进一步确认的点
- 确认仓库中新提交的 `build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh` 三个文件在 Git 中的权限位（`git ls-files -s` 查看是否为 100644 而非 100755）。从 PR diff 的 `b_mode` 字段均为 `100644`（非可执行）可确认此为根因。
- 确认 aarch64 架构 job 是否也会因相同原因失败（当前日志仅展示 amd64 构建，但 `.sh` 权限问题在两种架构上表现一致）。

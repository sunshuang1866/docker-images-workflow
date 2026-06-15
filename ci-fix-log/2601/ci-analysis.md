# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 脚本缺少执行权限
- 新模式症状关键词: Permission denied, exit code 126, COPY, .sh, b_mode, 100644

## 根因分析

### 直接错误
```
#14 0.070 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
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
- 失败原因: COPY 到镜像内的三个 `.sh` 脚本文件（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）没有可执行权限，Shell 无法直接通过 `./` 执行它们，报 `Permission denied`（exit code 126）。

### 与 PR 变更的关联
PR 新增了 Dockerfile 及三个构建脚本。从 diff 元数据可见，三个 `.sh` 文件的 `b_mode` 为 `100644`（即 `rw-r--r--`，无可执行位）。Dockerfile 中 `COPY` 指令会保留源文件权限，因此拷贝到镜像后脚本仍不可执行，而 `RUN` 中直接以 `./build-CTKAppLauncher.sh` 方式调用，触发权限拒绝错误。该失败由本次 PR 的变更直接引起。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `COPY` 指令之后、`RUN` 执行脚本之前，添加 `chmod +x` 命令为三个脚本赋予可执行权限：

```
RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh
```

或将 `.sh` 脚本在 git 仓库中的文件模式设为 `100755`（即可执行），使 `COPY` 到镜像后自带可执行权限。

### 方向 2（置信度: 高）
将 `RUN` 中的 `./build-CTKAppLauncher.sh` 改为 `bash ./build-CTKAppLauncher.sh`（通过显式调用 bash 解释器执行，无需脚本自身可执行权限），对另外两个脚本同理修改。

## 需要进一步确认的点
- 确认同一仓库中其他应用镜像（如同目录下 `5.8.1/24.03-lts-sp1/` 版本）的 `.sh` 脚本文件在 git 中的 mode 是否为 `100755`，以保持一致性。
- 确认 git 提交时的 `core.fileMode` 设置是否会屏蔽文件权限变更。

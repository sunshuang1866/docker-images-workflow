# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Shell脚本缺执行权限
- 新模式症状关键词: Permission denied, exit code: 126, COPY, chmod, +x

## 根因分析

### 直接错误
```
#13 [7/7] RUN ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ "amd64" = "arm64" ]; then         BRANCH="main";     fi &&     ./build-Slicer.sh v5.10.0
#13 0.065 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#13 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ \"$TARGETARCH\" = \"arm64\" ]; then         BRANCH=\"main\";     fi &&     ./build-Slicer.sh ${BRANCH}" did not complete successfully: exit code: 126
------
> [7/7] RUN ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ "amd64" = "arm64" ]; then         BRANCH="main";     fi &&     ./build-Slicer.sh v5.10.0:
0.065 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
------
Dockerfile:20
```

### 根因定位
- 失败位置: `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`:20
- 失败原因: 三个 Shell 构建脚本（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）通过 `COPY` 指令复制到镜像后**不具备可执行权限**（exit code 126 = 文件存在但不可执行），Dockerfile 中直接以 `./script.sh` 方式调用导致 `Permission denied`。

### 与 PR 变更的关联
**直接关联**。PR 新增的所有文件均为此次失败的直接原因：

1. 三个 `.sh` 脚本在 git 中的文件模式为 `100644`（不可执行），PR diff 中 `b_mode` 字段确认了这一点。
2. `Dockerfile:20-25` 中 `COPY` 后直接执行脚本，但缺少 `RUN chmod +x *.sh`（或等效的权限赋予步骤）来使脚本可执行。
3. Docker 的 `COPY` 指令保留源文件权限位；源文件本身无 x 位，导致镜像内文件同样无执行权限。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中 `COPY` 三个脚本后、`RUN` 执行脚本前，添加 `RUN chmod +x build-CTKAppLauncher.sh build-tbb.sh build-Slicer.sh` 赋予执行权限。

### 方向 2（置信度: 中）
在本地 git 仓库中将三个 `.sh` 文件的文件模式从 `644` 改为 `755`（`git update-index --chmod=+x`），使 `COPY` 进入镜像时即携带执行权限。方向 1 与方向 2 可任选其一，也可并用。

## 需要进一步确认的点
- 同仓库中其他已有容器镜像（如 `HPC/3dslicer/5.8.1/24.03-lts-sp1/`）是否也依赖 `.sh` 构建脚本，以及它们是如何处理执行权限的（可参考其 Dockerfile 确认惯例做法）。

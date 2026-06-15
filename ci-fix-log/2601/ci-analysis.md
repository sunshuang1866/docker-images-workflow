# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: COPY脚本缺执行权限
- 新模式症状关键词: `Permission denied`, `exit code: 126`, `COPY`, `.sh`

## 根因分析

### 直接错误
```
#13 [7/7] RUN ./build-CTKAppLauncher.sh && ./build-tbb.sh && if [ "amd64" = "arm64" ]; then BRANCH="main"; fi && ./build-Slicer.sh v5.10.0
#13 0.068 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#13 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh && ./build-tbb.sh && ..." did not complete successfully: exit code: 126
------
Dockerfile:20
```

### 根因定位
- 失败位置: `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`:20
- 失败原因: COPY 进容器的 `.sh` 脚本缺少可执行权限（`chmod +x`），导致 `./build-CTKAppLauncher.sh` 直接调用时 Permission denied，exit code 126

### 与 PR 变更的关联
PR 新增了 3 个构建脚本（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）并通过 `COPY` 指令放入镜像，随后在 `RUN` 中以 `./xxx.sh` 方式直接执行。这些脚本文件本身具备 `#!/bin/bash` shebang 且内容正确，但 `COPY` 指令不会自动赋予可执行权限——如果文件在 Git 仓库中未设置执行位（mode 100644），进入容器后权限仍为 644，shell 无法直接执行它们。三个构建脚本均有同样问题，只是首先执行到 `build-CTKAppLauncher.sh` 时即报错中断。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `COPY` 完成后、`RUN` 执行前，为所有被 COPY 的 `.sh` 脚本增加 `chmod +x` 步骤，确保脚本具备可执行权限后再调用 `./xxx.sh` 方式运行。具体可在 `RUN` 命令开头追加 `chmod +x *.sh`，或将每处 `./xxx.sh` 改为 `bash xxx.sh`（绕过可执行权限检查）。

### 方向 2（置信度: 高）
在本地 Git 仓库中为这三个 `.sh` 文件添加可执行权限（`git update-index --chmod=+x` 或 `chmod +x` 后提交），使得 `COPY` 进入容器时即带有可执行权限。此方式更简洁，无需修改 Dockerfile 逻辑。

## 需要进一步确认的点
- 当前仓库中这三个 `.sh` 文件的实际 Git 文件权限模式（期望为 100755，实际可能为 100644）。从 diff 中 `b_mode: '100644'` 可确认文件在仓库中确实是 100644 模式，即无执行位。此即为根因的直接证据，无需额外确认。

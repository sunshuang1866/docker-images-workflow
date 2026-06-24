# CI 失败分析报告

## 基本信息
- PR: #2725 — 【自动升级】3dslicer容器镜像升级至5.12.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: COPY脚本缺执行权限
- 新模式症状关键词: Permission denied, exit code 126, COPY, ./build, chmod

## 根因分析

### 直接错误
```
#14 [8/8] RUN ./build-CTKAppLauncher.sh && ./build-tbb.sh && ... && ./build-Slicer.sh v5.12.0 /opt/zlib.patch
#14 0.063 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#14 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh && ..." did not complete successfully: exit code: 126
------
Dockerfile:21
```

### 根因定位
- 失败位置: `HPC/3dslicer/5.12.0/24.03-lts-sp3/Dockerfile:21`（RUN 步骤）
- 失败原因: Dockerfile 通过 `COPY build-CTKAppLauncher.sh /opt/` 等指令将构建脚本复制到镜像内，但源文件在 Git 仓库中未设置可执行权限位（mode 未包含 execute bit），COPY 指令保留源文件权限，导致 `/opt/build-CTKAppLauncher.sh` 无执行权限，`./build-CTKAppLauncher.sh` 直接调用时报 "Permission denied"，exit code 126。

### 与 PR 变更的关联
PR 新增了 4 个 shell 脚本文件（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`、`zlib.patch`），并在 Dockerfile 中通过 `COPY` + `RUN ./xxx.sh` 的方式执行。所有脚本文件均为新增（`new_file: true`），且 Dockerfile 中未对 COPY 后的脚本执行 `chmod +x`。这是 PR 自身改动直接导致的构建失败。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `COPY` 指令之后、`RUN ./build-CTKAppLauncher.sh ...` 之前，增加一步 `RUN chmod +x /opt/*.sh` 确保所有构建脚本具有可执行权限。

### 方向 2（可选）
在 Git 仓库中将对应 `.sh` 文件的 mode 设置为可执行（`git update-index --chmod=+x`），使 COPY 进入镜像时天然携带执行权限。此方法需确认 CI 构建上下文中 git 文件权限位被正确保留。

## 需要进一步确认的点
- 确认同一目录下 `build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh` 三个文件的 Git 文件模式（`git ls-files -s`），验证当前是否为非可执行模式（`100644` 而非 `100755`）。
- 确认项目规范是否对 Dockerfile 中执行权限的处理方式有统一约定（是统一在 Dockerfile 中 `chmod`，还是在 Git 层面设置 `+x`）。

## 修复验证要求
无需外部验证。修改后重新触发 CI 构建，确认 `#14` 步骤不再出现 "Permission denied" 即可。

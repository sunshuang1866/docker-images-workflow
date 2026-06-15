# CI 失败分析报告

## 基本信息
- PR: #2601 — 【自动升级】3dslicer容器镜像升级至5.10.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: COPY脚本缺少执行权限
- 新模式症状关键词: Permission denied, COPY, chmod, exit code 126

## 根因分析

### 直接错误
```
#13 [7/7] RUN ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ "amd64" = "arm64" ]; then         BRANCH="main";     fi &&     ./build-Slicer.sh v5.10.0
#13 0.067 /bin/sh: line 1: ./build-CTKAppLauncher.sh: Permission denied
#13 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ \"$TARGETARCH\" = \"arm64\" ]; then         BRANCH=\"main\";     fi &&     ./build-Slicer.sh ${BRANCH}" did not complete successfully: exit code: 126
------
Dockerfile:20
```

### 根因定位
- 失败位置: HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile:20-25
- 失败原因: Dockerfile 中 `COPY` 了三个构建脚本（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）到 `/opt/`，但未执行 `chmod +x` 赋予执行权限，导致 `./build-CTKAppLauncher.sh` 时系统返回 `Permission denied`（exit code 126）。

### 与 PR 变更的关联
本次 PR 新增了完整的 Dockerfile 和三个构建脚本。Dockerfile 使用 `COPY` 指令将脚本复制到镜像内 `/opt/`，随后通过 `RUN` 指令直接执行这些脚本，但遗漏了 `chmod +x` 步骤。Docker `COPY` 默认保留源文件权限，若源文件无执行权限，则容器内同样无法执行。这是本次 PR 新引入的问题。

## 修复方向

### 方向 1（置信度: 高）
在三个 `COPY` 指令之后、`RUN ./build-CTKAppLauncher.sh ...` 之前，添加一个 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh` 步骤（或合并到同一个 RUN 层中），赋予脚本执行权限。

### 方向 2（置信度: 高）
也可以改用 `bash` 显式调用脚本，如 `bash ./build-CTKAppLauncher.sh`，但这不解决根本权限问题，且不如方向 1 清晰。推荐方向 1。

## 需要进一步确认的点
- 确认其他架构（arm64/aarch64）的构建 job 是否也因同样原因失败（日志中未提供下游架构 job 的输出）。

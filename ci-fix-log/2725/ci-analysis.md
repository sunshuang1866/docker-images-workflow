# CI 失败分析报告

## 基本信息
- PR: #2725 — 【自动升级】3dslicer容器镜像升级至5.12.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CMake版本过低
- 新模式症状关键词: `CMake 3.28.0 or higher is required`, `You are running version 3.27.9`, `cmake_minimum_required`

## 根因分析

### 直接错误
```
#15 43.26 CMake Error at CMakeLists.txt:15 (cmake_minimum_required):
#15 43.26   CMake 3.28.0 or higher is required.  You are running version 3.27.9
#15 43.26 
#15 43.26 
#15 43.26 -- Configuring incomplete, errors occurred!
#15 ERROR: process "/bin/sh -c ./build-CTKAppLauncher.sh &&     ./build-tbb.sh &&     if [ \"$TARGETARCH\" = \"arm64\" ]; then         BRANCH=\"main\";     fi &&     ./build-Slicer.sh ${BRANCH} /opt/zlib.patch" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:23-28`（`./build-Slicer.sh` 的 cmake 配置阶段）
- 失败原因: Slicer 5.12.0 源码的顶层 `CMakeLists.txt` 要求 CMake >= 3.28.0，而 openEuler 24.03-lts-sp3 基础镜像的 yum 源提供的 cmake 版本为 3.27.9，版本不满足上游要求。

### 与 PR 变更的关联
本次 PR 为新增的 Slicer 5.12.0 镜像构建。Dockerfile 中通过 `yum install cmake` 从系统源安装了 CMake 3.27.9，但 Slicer 5.12.0 的上游代码首次将 cmake_minimum_required 提升到了 3.28.0。CTKAppLauncher 和 TBB 的构建均成功完成（它们对 CMake 版本要求较低），失败发生在最后一步 `build-Slicer.sh` 的 cmake 配置阶段。

## 修复方向

### 方向 1（置信度: 高）
不从 yum 源安装 cmake，改用从 CMake 官方 GitHub Releases 下载预编译的 CMake 3.28+ 二进制包（如 3.28.1 或更高版本），在 Dockerfile 中将 `cmake` 从 yum install 列表中移除，并在构建脚本中单独安装/使用高版本 cmake。需同时考虑 amd64 和 arm64 两个架构的二进制文件名差异。

### 方向 2（置信度: 中）
若 openEuler 24.03-lts-sp3 有 epol 或其他附加源提供 cmake >= 3.28.0 的 RPM 包，可通过添加对应 yum 源来安装满足要求的 cmake 版本。

## 需要进一步确认的点
- 确认 openEuler 24.03-lts-sp3 的 yum 源或 EPOL 源是否提供 cmake >= 3.28.0 的 RPM 包
- 确认 Slicer 5.12.0 的 CMakeLists.txt 中 `cmake_minimum_required` 的具体版本要求（日志显示 3.28.0）
- 确认 CMake 官方 GitHub Releases 中适合 aarch64/arm64 架构的二进制包命名格式

## 修复验证要求
若选择方向 1（从 CMake 官方下载预编译二进制），code-fixer 必须：
1. 验证 https://github.com/Kitware/CMake/releases 上 cmake >= 3.28.0 的 Release 在 amd64 和 arm64 两个架构的二进制包均可下载
2. 确保 Dockerfile 中 `TARGETARCH` 变量与 cmake 二进制包架构标识正确对应（如 x86_64 / aarch64）

若选择方向 2（添加 yum 源），code-fixer 必须：
1. 在 openEuler 24.03-lts-sp3 容器中验证 `dnf install cmake` 在添加目标源后确实能安装 >= 3.28.0 版本
2. 确认该 yum 源在 CI 构建环境中可达

# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式10
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 327.8 -- Checking for module 'grpc++'
#12 327.9 --   Package 'grpc++', required by 'virtual:world', not found
#12 327.9 CMake Error at /usr/share/cmake/Modules/FindPkgConfig.cmake:607 (message):
#12 327.9   A required package was not found
#12 327.9 Call Stack (most recent call first):
#12 327.9   /usr/share/cmake/Modules/FindPkgConfig.cmake:829 (_pkg_check_modules_internal)
#12 327.9   src/CMakeLists.txt:1055 (pkg_check_modules)
#12 327.9
#12 327.9 -- Configuring incomplete, errors occurred!
#12 327.9 + exit 1
```

### 根因定位
- 失败位置: `src/CMakeLists.txt:1055`（ceph 源码内）
- 失败原因: Dockerfile 的 `dnf install` 步骤遗漏了 gRPC C++ 开发库（`grpc-devel` / `grpc++-devel`），导致 cmake 配置阶段 `pkg_check_modules` 找不到 `grpc++` 包

### 与 PR 变更的关联
本次 PR 新增了 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`，其 `dnf install -y` 命令中列出了大量依赖包，但缺少 ceph 21.3.0 编译所需的 `grpc-devel` 和 `grpc++-devel`（或 openEuler 24.03-lts-sp3 上对应的 gRPC 开发包）。失败是由 PR 新增 Dockerfile 的依赖声明不完整直接触发的。

此外日志末尾出现的两条 BuildKit 警告：
- `FromAsCasing`: `FROM $BASE as builder` 中 `as` 应大写为 `AS`（模式无关，仅风格提示）
- `UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH'` (line 47): `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 自引用了未定义变量，匹配 **模式20**

这两条警告是次要问题，不是本次失败的直接原因，但仍建议修复。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 4 行附近的 `dnf install -y` 命令中补充 gRPC 相关的开发包。openEuler 24.03-lts-sp3 上对应的包名可能为 `grpc-devel`、`grpc++-devel` 或 `protobuf-devel`（含 grpc 子包）。需根据 openEuler 24.03-lts-sp3 仓库实际情况确认精确包名并加入安装列表。

### 方向 2（置信度: 中）
同时修复第 47 行 `ENV LD_LIBRARY_PATH` 的模式20问题：将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`，以及第 2 行 `as builder` 改为 `AS builder`。

## 需要进一步确认的点
- openEuler 24.03-lts-sp3 上提供 `grpc++` pkg-config 模块的精确包名（可能是 `grpc-devel`、`grpc++-devel` 或 `grpc-plugins-devel`）
- ceph 21.3.0 是否对 gRPC/protobuf 有特定最低版本要求，以及 openEuler 仓库中的版本是否满足

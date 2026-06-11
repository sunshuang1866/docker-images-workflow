# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 364.6 -- Checking for module 'grpc++'
#12 364.6 --   Package 'grpc++', required by 'virtual:world', not found
#12 364.6 CMake Error at /usr/share/cmake/Modules/FindPkgConfig.cmake:607 (message):
#12 364.6   A required package was not found
#12 364.6 Call Stack (most recent call first):
#12 364.6   /usr/share/cmake/Modules/FindPkgConfig.cmake:829 (_pkg_check_modules_internal)
#12 364.6   src/CMakeLists.txt:1055 (pkg_check_modules)
#12 364.6
#12 364.6
#12 364.6 -- Configuring incomplete, errors occurred!
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile:41`（`do_cmake.sh` cmake 配置阶段）
- 失败原因: Ceph 21.3.0 的 CMake 构建系统要求 `grpc++` 包（gRPC C++ 库），但 Dockerfile 的 `dnf install` 列表中遗漏了对应的 `grpc-devel`（或 `grpc-plugins`/`grpc-cpp-devel`）包

### 与 PR 变更的关联
PR 新增了 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`，该 Dockerfile 在 `dnf install` 命令中列举了大量编译依赖，但遗漏了 `grpc++` 相关的开发包。Ceph 21.3.0 的 CMakeLists.txt（第 1055 行）通过 `pkg_check_modules` 强制要求 `grpc++`，缺少该依赖导致 cmake 配置阶段直接失败。此失败完全由本次 PR 的 Dockerfile 内容引起。

**附注：** 日志末尾还有一个 BuildKit 警告（`UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH'`），匹配模式20，但该警告不是构建失败的原因，不影响根因判断。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install` 命令中补充 gRPC C++ 相关的开发包。在 openEuler 24.03-LTS-SP3 上，可能的包名为 `grpc-devel`、`grpc-plugins` 或 `grpc-cpp-devel`。需要确认 openEuler 仓库中提供 gRPC C++ 开发文件的准确包名并添加到安装列表中。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP3 软件仓库中提供 `grpc++` pkg-config 模块的准确包名（可能是 `grpc-devel`、`grpc-cpp-devel` 或 `grpc-plugins`）
2. Ceph 21.3.0 是否还依赖其他 gRPC 相关组件（如 `grpc`、`protobuf`），虽然在 openEuler 中 protobuf 的 CMake 模块已有（日志中 `Found Protobuf: /usr/lib64/libprotobuf.so` 显示通过），但 protobuf-devel 可能也需要显式声明

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
#12 401.0 -- Found Protobuf: /usr/lib64/libprotobuf.so (found version "4.25.1")
#12 401.0 -- Checking for module 'grpc++'
#12 401.0 --   Found grpc++, version 1.60.0
#12 401.2 -- Using gRPC 1.60.0 (via pkg-config)
#12 401.2 CMake Error at src/CMakeLists.txt:1058 (find_program):
#12 401.2   Could not find _GRPC_CPP_PLUGIN_EXECUTABLE using the following names:
#12 401.2   grpc_cpp_plugin
#12 401.2 
#12 401.2 
#12 401.3 -- Configuring incomplete, errors occurred!
#12 401.3 + exit 1
```

### 根因定位
- 失败位置: Dockerfile:41 (`./do_cmake.sh ...` → cmake 配置阶段)
- 失败原因: Dockerfile 的 `dnf install` 步骤遗漏了 `grpc-plugins` 包，导致 cmake 配置时找不到 `grpc_cpp_plugin` 可执行文件

### 与 PR 变更的关联
PR 新增了整个 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`（54 行全新文件）。该 Dockerfile 的 `dnf install` 命令行中安装了 gRPC 运行时库（通过依赖间接引入，日志显示 `grpc++` 1.60.0 已找到），但**未显式安装 `grpc-plugins` 包**（该包提供 `grpc_cpp_plugin` 编译器插件）。Ceph 的 cmake 配置脚本在检测到 gRPC 后，尝试进一步查找 protobuf 的 gRPC C++ 代码生成插件，因缺失而失败。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 3 行 `dnf install -y` 的包列表中补充 `grpc-plugins`（或 openEuler 24.03 中对应提供 `grpc_cpp_plugin` 的包名，通常为 `grpc-plugins` 或 `grpc-devel` 中包含）。补完后 cmake 配置应能顺利通过。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP3 中提供 `grpc_cpp_plugin` 可执行文件的确切包名（可能为 `grpc-plugins`、`grpc-devel` 或 `grpc` 子包），建议在 openEuler 环境中 `dnf provides */grpc_cpp_plugin` 确认后写入 Dockerfile。
- Dockerfile 中有两个 BuildKit 警告（`FromAsCasing` 和 `UndefinedVar`）虽然不阻塞构建，但建议一并修正：`as builder` → `AS builder`，`$LD_LIBRARY_PATH` → `${LD_LIBRARY_PATH:-}`。

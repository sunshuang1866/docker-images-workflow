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
#12 405.8 -- Using gRPC 1.60.0 (via pkg-config)
#12 405.8 CMake Error at src/CMakeLists.txt:1058 (find_program):
#12 405.8   Could not find _GRPC_CPP_PLUGIN_EXECUTABLE using the following names:
#12 405.8   grpc_cpp_plugin
#12 405.8
#12 405.8
#12 405.8 -- Configuring incomplete, errors occurred!
#12 405.8 + exit 1
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile:41`（`RUN git clone ... ceph ... && ./do_cmake.sh ...` 中的 cmake 配置步骤）
- 失败原因: Ceph 编译的 cmake 配置阶段找不到 `grpc_cpp_plugin` 可执行文件，该工具是 protobuf/gRPC 代码生成所需的编译器插件。

### 与 PR 变更的关联
**与 PR 直接相关**。本次 PR 新增了 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`，在 `dnf install` 依赖列表中遗漏了提供 `grpc_cpp_plugin` 的包。虽然 `grpc++` 库本身作为某些包的传递依赖被自动安装（cmake 能找到 `grpc++`），但 `grpc_cpp_plugin` 二进制文件位于单独的开发工具包中，未被显式声明安装。

此外，日志末尾有一个非致命警告：
```
- UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 48)
```
这属于**模式20**（ENV 自引用未定义变量），不影响构建结果，但应在后续一并修正。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install` 步骤中添加提供 `grpc_cpp_plugin` 的包。在 openEuler 24.03-LTS-SP3 上，该二进制文件通常由 `grpc-devel` 或 `grpc-plugins` 包提供。具体包名可通过 `dnf provides */grpc_cpp_plugin` 确认。

### 方向 2（置信度: 中，非致命警告修复）
将 Dockerfile 第 48 行 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 改为 `ENV LD_LIBRARY_PATH=/usr/local/lib64:${LD_LIBRARY_PATH:-}`，消除 BuildKit 的 UndefinedVar 警告（参考模式20）。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP3 上提供 `grpc_cpp_plugin` 二进制的确切 RPM 包名（`grpc-devel`、`grpc-plugins` 或 `protobuf-compiler`）。
2. 除 `grpc_cpp_plugin` 外，是否还缺少其他 protobuf/gRPC 相关工具（如 `protoc`），确认 cmake 日志中没有后续的类似报错。

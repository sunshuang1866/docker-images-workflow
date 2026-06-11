# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10（缺少构建依赖）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 287.8 -- Found Protobuf: /usr/lib64/libprotobuf.so (found version "4.25.1")
#12 287.8 -- Checking for module 'grpc++'
#12 287.8 --   Found grpc++, version 1.60.0
#12 288.1 -- Using gRPC 1.60.0 (via pkg-config)
#12 288.1 CMake Error at src/CMakeLists.txt:1058 (find_program):
#12 288.1   Could not find _GRPC_CPP_PLUGIN_EXECUTABLE using the following names:
#12 288.1   grpc_cpp_plugin
#12 288.1
#12 288.1
#12 288.1 -- Configuring incomplete, errors occurred!
#12 288.1 + exit 1
#12 ERROR: process "/bin/sh -c git clone -b v${VERSION} ... ./do_cmake.sh ... ninja ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Ceph 构建的 CMake 配置阶段，`src/CMakeLists.txt:1058`（`find_program` 查找 `grpc_cpp_plugin`）
- 失败原因: Dockerfile 的 `dnf install` 中缺少 `grpc-plugins` 包（提供 `grpc_cpp_plugin` 可执行文件），导致 CMake 配置阶段因找不到 gRPC C++ protobuf 编译器插件而失败

### 与 PR 变更的关联
PR 新增了 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`，该 Dockerfile 的 `dnf install` 命令中安装了 protobuf 和 gRPC 运行库（作为 `thrift-devel` 等包传递依赖自动安装），但遗漏了编译所需的 `grpc-plugins` 包。Ceph 21.3.0 的构建系统需要 `grpc_cpp_plugin` 来从 `.proto` 文件生成 C++ gRPC 代码。这是**由本次 PR 新增代码直接引发**的构建失败。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 4 行的 `dnf install` 命令中补充 `grpc-plugins` 包，使 `grpc_cpp_plugin` 可执行文件在 CMake 配置时可用。同时建议一并检查是否需要 `protobuf-compiler` 和 `grpc-devel` 以确保 gRPC/protobuf 全套编译工具链完整。

### 方向 2（置信度: 中）
如果 `grpc-plugins` 包在 openEuler 24.03-LTS-SP3 中不可用或版本不匹配，可通过 pip 安装 `grpcio-tools` 并从 Python 环境中获取 `grpc_cpp_plugin`，或在 Ceph 源码目录中设置 `-D_GRPC_CPP_PLUGIN_EXECUTABLE` CMake 变量指向自定义路径。

## 需要进一步确认的点
1. **openEuler 24.03-LTS-SP3 仓库中 `grpc-plugins` 包的准确名称**：需确认是 `grpc-plugins`、`grpc-devel` 还是其他包名提供 `grpc_cpp_plugin` 可执行文件。可用 `dnf provides */grpc_cpp_plugin` 查询。
2. **附加 Dockerfile 警告**：日志末尾有两条 BuildKit 警告（`FromAsCasing`、`UndefinedVar`）与 **模式20** 匹配，虽非本次失败根因，但建议一并修正：第 2 行 `FROM $BASE as builder` 的 `as` 应与 `FROM` 大小写一致；第 47 行 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 应改为 `${LD_LIBRARY_PATH:-}` 避免自引用未定义变量。

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
#12 364.9 CMake Error at /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:230 (message):
#12 364.9   Could NOT find Protobuf (missing: Protobuf_LIBRARIES Protobuf_INCLUDE_DIR)
#12 364.9 Call Stack (most recent call first):
#12 364.9   /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)
#12 364.9   /usr/share/cmake/Modules/FindProtobuf.cmake:652 (FIND_PACKAGE_HANDLE_STANDARD_ARGS)
#12 364.9   src/CMakeLists.txt:1029 (find_package)
#12 364.9
#12 364.9 -- Configuring incomplete, errors occurred!
#12 364.9 + exit 1
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:17（dnf install 行）
- 失败原因: Dockerfile 的 `dnf install` 步骤遗漏了 ceph 编译所需的 `protobuf` 和 `protobuf-devel` 包，导致 ceph cmake 配置阶段 `find_package(Protobuf)` 失败。

### 与 PR 变更的关联
PR 新增了 ceph 21.3.0 的 Dockerfile（54 行新增），其中 `dnf install` 命令（第 4-17 行）安装了大量编译依赖，但遗漏了 `protobuf protobuf-devel`。ceph 源码中的 `src/CMakeLists.txt:1029` 调用 `find_package(Protobuf)` 需要这些包。这是 PR 引入的新 Dockerfile 直接导致的构建失败，与历史 20.3.0 版本无关。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第一个 `RUN dnf install -y` 步骤中添加 `protobuf protobuf-devel` 包。ceph 构建依赖 protobuf 库和头文件，cmake 的 `FindProtobuf` 模块需要 `Protobuf_LIBRARIES` 和 `Protobuf_INCLUDE_DIR`，这些由 `protobuf-devel` 提供。

### 方向 2（置信度: 中）
Dockerfile 第 48 行 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 存在自引用未定义变量问题（匹配模式20）。虽然当前这是 BuildKit 警告而非失败原因，但建议将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}` 以消除警告，避免未来 BuildKit 版本对此类引用的处理更严格。

## 需要进一步确认的点
- 需要确认 `protobuf` 和 `protobuf-devel` 在 openEuler 24.03-LTS-SP3 仓库中的确切包名（`dnf search protobuf`），通常为 `protobuf`、`protobuf-devel`，但也可能是 `protobuf-c`、`protobuf-c-devel` 或 `protobuf-compiler`，具体取决于 ceph 对 protobuf C++ API 还是 protobuf-c 的依赖。
- 日志中还有 `jq: command not found` 的非致命报错（`#12 364.5`），虽不影响当前构建，但若 `do_cmake.sh` 后续逻辑依赖 `jq` 解析 JSON 则可能成为隐患，可视需要安装 `jq`。

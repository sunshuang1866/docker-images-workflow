# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式10
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 342.9 CMake Error at /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:230 (message):
#12 342.9   Could NOT find Protobuf (missing: Protobuf_LIBRARIES Protobuf_INCLUDE_DIR)
#12 342.9 Call Stack (most recent call first):
#12 342.9   /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)
#12 342.9   /usr/share/cmake/Modules/FindProtobuf.cmake:652 (FIND_PACKAGE_HANDLE_STANDARD_ARGS)
#12 342.9   src/CMakeLists.txt:1029 (find_package)
#12 342.9
#12 342.9
#12 342.9 -- Configuring incomplete, errors occurred!
#12 342.9 + exit 1
#12 ERROR: process "/bin/sh -c git clone -b v${VERSION} --recursive --depth 1 https://github.com/ceph/ceph.git     && cd ceph     && ./do_cmake.sh -DCMAKE_BUILD_TYPE=Release -DWITH_TESTS=OFF     && cd build     && ninja -j$(nproc)     && ninja install" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:30-32（`./do_cmake.sh` 执行的 cmake 配置阶段）
- 失败原因: Dockerfile 的 `dnf install` 依赖列表中遗漏了 `protobuf-devel`（或 `protobuf-compiler`），导致 ceph 21.3.0 的 CMake 配置阶段找不到 Protobuf 库和头文件

### 与 PR 变更的关联
PR 新增了 Ceph 21.3.0 的 Dockerfile（`Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`），其中 `dnf install` 命令列出了 30+ 个依赖包，但未包含 `protobuf-devel`。Ceph 21.3.0 的构建系统（`src/CMakeLists.txt:1029`）通过 `find_package(Protobuf ...)` 强制要求 Protobuf，由于缺失该依赖导致 CMake 配置失败。该失败由本次 PR 的 Dockerfile 依赖声明不完备直接触发。

附：Dockerfile 中还有两个非致命问题：
- 第 2 行：`FROM $BASE as builder` — `as` 与 `FROM` 大小写不一致（BuildKit `FromAsCasing` 警告）
- 第 47 行：`ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` — 首次定义时自引用未定义变量 `$LD_LIBRARY_PATH`，匹配 **模式20**（BuildKit `UndefinedVar` 警告）

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 4-20 行的 `dnf install` 命令中补充 Protobuf 相关依赖包：对于 openEuler 24.03-LTS-SP3，需安装 `protobuf-devel`（提供 `Protobuf_INCLUDE_DIR` 和 `Protobuf_LIBRARIES`）以及 `protobuf-compiler`（提供 `protoc` 编译器）。参照模式10 中"缺少构建依赖"类问题，根据 CMake 报错的库名补充对应的 `-devel` 包即可。

### 方向 2（置信度: 中）
修正 ENV 自引用问题（模式20）：将第 47 行 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 改为 `ENV LD_LIBRARY_PATH=/usr/local/lib64:${LD_LIBRARY_PATH:-}`，消除 BuildKit 的 `UndefinedVar` 警告（该警告本身不导致构建失败，但属于非规范用法）。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP3 软件仓库中 `protobuf-devel` / `protobuf-compiler` 的确切包名（可能为 `protobuf-devel`、`protobuf-compiler`，或统一在 `protobuf` 包中）
- 确认 ceph 21.3.0 对 Protobuf 的最低版本要求，以及 openEuler 24.03-LTS-SP3 仓库提供的 Protobuf 版本是否满足该要求
- 确认是否还有其他 ceph 21.3.0 强制要求但 Dockerfile 中尚未列出的 `-devel` 依赖（如 CMake 配置阶段后续可能还会报其他 `Could NOT find` 错误）

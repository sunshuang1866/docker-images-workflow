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
#12 322.2 CMake Error at /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:230 (message):
#12 322.2   Could NOT find Protobuf (missing: Protobuf_LIBRARIES Protobuf_INCLUDE_DIR)
#12 322.2 Call Stack (most recent call first):
#12 322.2   /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)
#12 322.2   /usr/share/cmake/Modules/FindProtobuf.cmake:652 (FIND_PACKAGE_HANDLE_STANDARD_ARGS)
#12 322.2   src/CMakeLists.txt:1029 (find_package)
#12 322.2 
#12 322.2 
#12 322.3 -- Configuring incomplete, errors occurred!
#12 322.3 + exit 1
#12 ERROR: process "/bin/sh -c git clone -b v${VERSION} --recursive --depth 1 https://github.com/ceph/ceph.git     && cd ceph     && ./do_cmake.sh -DCMAKE_BUILD_TYPE=Release -DWITH_TESTS=OFF     && cd build     && ninja -j$(nproc)     && ninja install" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:40 (RUN git clone ... && ./do_cmake.sh ... 步骤)
- 失败原因: Ceph CMake 构建系统的 `src/CMakeLists.txt:1029` 调用 `find_package(Protobuf)` 时，系统未安装 `protobuf-devel` 开发包，导致 CMake 配置阶段失败，编译无法进行。

### 与 PR 变更的关联
PR 新增了 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`，其 `dnf install` 步骤缺少 `protobuf-devel`（以及可能需要的 `protobuf-compiler`）包。这是 Ceph 21.3.0 的新增编译依赖（旧版本 Dockerfile 如 `20.3.0/24.03-lts-sp2/` 可能不依赖 Protobuf，或其依赖链通过其他包间接引入）。此失败是 PR 改动直接引入的。

**附注**：日志中还存在两个非致命的 BuildKit 警告：
1. `FromAsCasing`：第2行 `FROM $BASE as builder` 应写为 `FROM $BASE AS builder`（关键字大小写不一致）
2. `UndefinedVar`（匹配模式20）：第47行 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 在 builder stage 首次定义时自引用了未定义的 `$LD_LIBRARY_PATH`，应改为 `${LD_LIBRARY_PATH:-}`

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install` 命令中补充 `protobuf-devel` 包（以及 `protobuf-compiler`，如果 ceph build 需要 protoc 编译器）。同时修正两个 BuildKit 警告：将 `as` 改为 `AS`，将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`。

### 方向 2（置信度: 中）
如果补充 `protobuf-devel` 后仍报其他依赖缺失（如 `gperftools-devel`、`ncurses-devel` 等日志中出现的 `Could NOT find` 项），需逐一补充对应的 `-devel` 包。日志中还出现了 `gperftools`、`JeMalloc`、`xfs`、`Curses` 等未找到的提示（当前均为非致命，CMake 有 fallback 或可选跳过），但 Ceph 21.3.0 的某些组件可能后续强制要求这些库。

## 需要进一步确认的点
1. 确认 Ceph 21.3.0 的完整编译依赖列表（查阅上游 `src/CMakeLists.txt` 中的 `find_package` 调用），确保所有必需的 `-devel` 包均已安装。
2. 确认 `protobuf-devel` 在 openEuler 24.03-LTS-SP3 仓库中的确切包名（可能是 `protobuf-devel` 或 `protobuf`）。
3. 日志中 `jq: command not found`（#12 321.9 行）虽然当前未导致失败，但应确认 Ceph CMake 脚本在后续步骤中是否依赖 `jq`，如需要则补充安装 `jq` 包。

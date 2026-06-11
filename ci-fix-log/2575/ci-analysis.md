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
#12 277.9 CMake Error at /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:230 (message):
#12 277.9   Could NOT find Protobuf (missing: Protobuf_LIBRARIES Protobuf_INCLUDE_DIR)
#12 277.9 Call Stack (most recent call first):
#12 277.9   /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)
#12 277.9   /usr/share/cmake/Modules/FindProtobuf.cmake:652 (FIND_PACKAGE_HANDLE_STANDARD_ARGS)
#12 277.9   src/CMakeLists.txt:1029 (find_package)
#12 277.9
#12 277.9 -- Configuring incomplete, errors occurred!
#12 278.0 + exit 1
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:41（`RUN git clone ... && ./do_cmake.sh ...` 行中的 cmake 配置步骤）
- 失败原因: Dockerfile 的 `dnf install` 阶段遗漏了 `protobuf-devel`（及可能 `protobuf-compiler`）包，导致 cmake 配置阶段 `find_package(Protobuf)` 找不到 Protobuf 库和头文件。

### 与 PR 变更的关联
PR 新增了完整的 ceph 21.3.0 Dockerfile（54 行），这是一个全新的文件。Dockerfile 中的 `dnf install` 列表未包含 `protobuf-devel`，而 ceph 21.3.0 的 cmake 构建系统要求 Protobuf 作为编译依赖。**失败完全由本次 PR 的 Dockerfile 内容直接触发**。

另外，日志中同时暴露了两个次要问题：
1. **模式20**：`ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH`（Dockerfile:48）自引用了未定义的变量，产生 `UndefinedVar` 警告。
2. `FromAsCasing` 警告：Dockerfile:2 中 `as` 关键词与 `FROM` 关键词大小写不一致。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install -y` 列表中添加 `protobuf-devel` 包（openEuler 中 protobuf 开发包的包名）。根据 ceph 构建的需要，可能还需同时添加 `protobuf-compiler`。

### 方向 2（置信度: 中）
将 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 改为 `ENV LD_LIBRARY_PATH=/usr/local/lib64:${LD_LIBRARY_PATH:-}`，消除 BuildKit 的 `UndefinedVar` 警告（参考模式20）。

## 需要进一步确认的点
- 确认 openEuler 24.03-lts-sp3 中 protobuf 相关包的确切名称（`protobuf-devel` 与 `protobuf-compiler` 的包名和可用性）。
- 确认 ceph 21.3.0 对 protobuf 的最低版本要求，确保仓库中的 protobuf 版本满足条件。
- 日志中 `Could NOT find xfs`、`Could NOT find gperftools`、`Could NOT find JeMalloc`、`Could NOT find Curses` 均为非致命告警（cmake 有对应 fallback），但建议一并审查是否需要补全这些依赖以避免功能缺失。

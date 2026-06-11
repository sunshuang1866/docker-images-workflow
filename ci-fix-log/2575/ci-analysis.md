# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

## 根因分析

### 直接错误
```
#12 280.4 CMake Error at /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:230 (message):
#12 280.4   Could NOT find Protobuf (missing: Protobuf_LIBRARIES Protobuf_INCLUDE_DIR)
#12 280.4 Call Stack (most recent call first):
#12 280.4   /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)
#12 280.4   /usr/share/cmake/Modules/FindProtobuf.cmake:652 (FIND_PACKAGE_HANDLE_STANDARD_ARGS)
#12 280.4   src/CMakeLists.txt:1029 (find_package)
#12 280.5 -- Configuring incomplete, errors occurred!
#12 280.5 + exit 1
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:40-45 (RUN git clone ... cmake 步骤)
- 失败原因: Dockerfile 的 `dnf install` 命令中缺少 `protobuf-devel` 包，导致 CMake 配置阶段 `find_package(Protobuf)` 找不到 Protobuf 库和头文件

### 与 PR 变更的关联
PR 新增了完整的 Dockerfile（54 行）和 entrypoint.sh（72 行）。Dockerfile 中的 `dnf install` 列表遗漏了 `protobuf-devel`（以及可能需要的 `protobuf-compiler`），这是 ceph 21.3.0 版本 CMake 构建的必需依赖，而之前版本的 ceph（如 20.3.0）可能未引入该依赖。该失败**由本次 PR 的 Dockerfile 变更直接引起**。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 5-14 行的 `dnf install` 命令中补充 `protobuf-devel`（可能还需 `protobuf-compiler`），例如将：
```
libev-devel fuse3-devel bash-completion
```
改为：
```
libev-devel fuse3-devel bash-completion protobuf-devel protobuf-compiler
```

### 方向 2（置信度: 低）
日志中同时存在 BuildKit `UndefinedVar` 警告（匹配模式20）：`ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 自引用了尚未存在的变量。虽然这不影响构建结果，为使构建干净，可将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`。

## 需要进一步确认的点
- 确认 ceph 21.3.0 的 `src/CMakeLists.txt:1029` 处 `find_package(Protobuf)` 的具体要求（是否需要指定最低版本），以判断是否只需 `protobuf-devel` 还是需要特定版本
- 日志中另有 `Could NOT find Curses (missing: CURSES_LIBRARY CURSES_INCLUDE_PATH)` 信息，虽未导致 CMake 报 fatal error，但在修复完成后应确认是否影响 ceph 的某些可选功能

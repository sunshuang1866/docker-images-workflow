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
#12 331.5 CMake Error at /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:230 (message):
#12 331.5   Could NOT find Protobuf (missing: Protobuf_LIBRARIES Protobuf_INCLUDE_DIR)
#12 331.5 Call Stack (most recent call first):
#12 331.5   /usr/share/cmake/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)
#12 331.5   /usr/share/cmake/Modules/FindProtobuf.cmake:652 (FIND_PACKAGE_HANDLE_STANDARD_ARGS)
#12 331.5   src/CMakeLists.txt:1029 (find_package)
#12 331.5
#12 331.5 -- Configuring incomplete, errors occurred!
#12 331.5 + exit 1
#12 ERROR: process "/bin/sh -c git clone -b v${VERSION} --recursive --depth 1 https://github.com/ceph/ceph.git     && cd ceph     && ./do_cmake.sh -DCMAKE_BUILD_TYPE=Release -DWITH_TESTS=OFF     && cd build     && ninja -j$(nproc)     && ninja install" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:40（`RUN git clone ...` 行，cmake 配置阶段）
- 失败原因: Ceph 21.3.0 的 CMake 构建系统要求 Protobuf 库及头文件，但 Dockerfile 的 `dnf install` 步骤遗漏了 `protobuf-devel` 包（可能还需 `protobuf-compiler`），导致 cmake 配置阶段报 `Could NOT find Protobuf` 并终止构建。

### 与 PR 变更的关联
PR 新增了 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`（全新文件，54 行），其中 `dnf install` 命令的依赖列表未包含 Protobuf 相关的开发包。Ceph 21.3.0 对 Protobuf 有编译依赖，缺失该包直接导致 cmake 配置失败。此失败与 PR 变更直接相关。

### 次要问题
日志中另有两个 BuildKit 警告（不影响构建成败，但宜一并修正）：

1. **UndefinedVar**（匹配模式20）：`ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 在首次定义 `LD_LIBRARY_PATH` 时自引用了未定义的变量。应将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`。
2. **FromAsCasing**：Dockerfile 第 2 行 `FROM $BASE as builder` 中 `as` 为小写，BuildKit 建议统一大写为 `AS`。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第一个 `dnf install` 命令中补充 Protobuf 相关依赖包：添加 `protobuf-devel` 和 `protobuf-compiler`（Ceph 编译通常需要 protoc 编译器和 Protobuf 库/头文件）。参考 openEuler 24.03-LTS-SP3 仓库中对应的包名，将缺失包追加到 `dnf install` 列表中。

### 方向 2（置信度: 中）
若仅补充 `protobuf-devel` 仍报错，可能需要同时安装 `protobuf` 运行时包以及检查 Ceph 所需的最低 Protobuf 版本是否在 openEuler 24.03-LTS-SP3 的仓库中可用。CMake 日志中未显示版本不匹配，置信度为中。

## 需要进一步确认的点
- Ceph 21.3.0 在 openEuler 24.03-LTS-SP3 仓库中 Protobuf 包的准确包名和版本（当前为 `protobuf`/`protobuf-devel`/`protobuf-compiler`，需确认与 Ceph 21.3.0 的版本兼容性）。
- 除 Protobuf 外，Ceph 21.3.0 是否还有其他被 cmake `Could NOT find` 报告的缺失依赖（本次日志显示 `xfs`、`gperftools`、`JeMalloc`、`Curses` 也为未找到状态，但这些可能是可选依赖，cmake 未将其标记为 Error）。

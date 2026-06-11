# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10 (缺少构建依赖) + 模式20 (ENV自引用未定义变量)
- 新模式标题: N/A
- 新模式症状关键词: N/A

## 根因分析

### 直接错误
```
#12 1400.2 -- Checking for module 'grpc++'
#12 1400.2 --   Package 'grpc++', required by 'virtual:world', not found
#12 1400.2 CMake Error at /usr/share/cmake/Modules/FindPkgConfig.cmake:607 (message):
#12 1400.2   A required package was not found
#12 1400.2 Call Stack (most recent call first):
#12 1400.2   /usr/share/cmake/Modules/FindPkgConfig.cmake:829 (_pkg_check_modules_internal)
#12 1400.2   src/CMakeLists.txt:1055 (pkg_check_modules)
#12 1400.2 
#12 1400.2 
#12 1400.2 -- Configuring incomplete, errors occurred!
#12 1400.3 + exit 1
#12 ERROR: process "/bin/sh -c git clone -b v${VERSION} --recursive --depth 1 ..." did not complete successfully: exit code: 1
```

另外存在一条 BuildKit 警告（非致命，但需修复）：
```
UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 48)
```

### 根因定位
- 失败位置: ceph 源码 `src/CMakeLists.txt:1055`，cmake 通过 pkg-config 查找 `grpc++` 失败
- 失败原因: Dockerfile 的 `dnf install` 步骤遗漏了 `grpc-devel`（gRPC C++ 开发库）包，导致 cmake 配置阶段 `pkg_check_modules(grpc++)` 检测不到

### 与 PR 变更的关联
PR 变更新增了 ceph 21.3.0 的 Dockerfile。ceph 21.3.0 相比 20.3.0 新增了对 gRPC C++ 的构建依赖，而新的 Dockerfile 的 `dnf install` 列表沿用旧版本依赖清单，未追加 `grpc-devel` 相关包，直接触发了 cmake 配置失败。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 9-24 行的 `dnf install` 命令中补充 gRPC C++ 开发包。需确认 openEuler 24.03-LTS-SP3 仓库中的准确包名（通常为 `grpc-devel` 或 `grpc++-devel`），添加到安装列表中。

### 方向 2（置信度: 高）
Dockerfile 第 48 行的 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 存在自引用未定义变量问题（模式20），应将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`，消除 BuildKit 的 UndefinedVar 警告。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP3 中 gRPC C++ 开发库的准确包名（`dnf search grpc` 确认是 `grpc-devel`、`grpc++-devel` 还是 `libgrpc-devel`）
- 确认 ceph 21.3.0 `do_cmake.sh` 是否还有其他新增依赖（`gperftools` 和 `JeMalloc` 在日志中也显示 `Could NOT find`，但目前仅产生 Warning 回退到 libc，需确认是否为 21.3.0 的新要求）

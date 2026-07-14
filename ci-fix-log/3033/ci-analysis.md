# CI 失败分析报告

## 基本信息
- PR: #3033 — chore(seissol): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: x86专属编译标志
- 新模式症状关键词: unrecognized command-line option, -mno-red-zone, -mno-vzeroupper, aarch64, SeisSol

## 根因分析

### 直接错误
```
#14 55.53 c++: error: unrecognized command-line option '-mno-red-zone'
#14 55.53 gmake[2]: *** [CMakeFiles/SeisSol-lib.dir/build.make:358: CMakeFiles/SeisSol-lib.dir/src/generated_code/subroutine.cpp.o] Error 1
#14 83.94 gmake[1]: *** [CMakeFiles/Makefile2:100: CMakeFiles/SeisSol-lib.dir/all] Error 2
#14 83.94 gmake: *** [Makefile:91: all] Error 2
```

### 根因定位
- 失败位置: SeisSol 构建阶段，文件 `CMakeFiles/SeisSol-lib.dir/src/generated_code/subroutine.cpp.o`
- 失败原因: SeisSol 上游源码的 CMake 构建系统向编译命令中注入了 `-mno-red-zone` 标志，该标志是 x86_64 架构专属的 GCC 选项。CI 在 aarch64（ARM64） runner 上构建时，GCC 12 无法识别该选项，导致编译失败。日志中 PARMETIS 构建路径（`Linux-aarch64`）进一步确认编译发生在 aarch64 架构上。

### 与 PR 变更的关联
**直接相关**。PR 新增了 `HPC/seissol/202103.Sumatra/24.03-lts-sp4/Dockerfile`，并通过 `meta.yml` 声明该镜像支持 `amd64` 和 `arm64` 两种架构。CI 在两个架构上并行构建：x86_64 构建通过（`-mno-red-zone` 有效），aarch64 构建失败（该标志不被识别）。Dockerfile 中虽然传入了 `-DHOST_ARCH=noarch`，但该参数仅禁用了 CPU 特性优化（`-march`），并未阻止 CMakeLists.txt 中硬编码的 x86_64 专属编译标志被注入。

此外，日志中还出现了一个次级问题：`UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 98)`，匹配**模式20**。该警告不影响构建成败，但应一并修复。

## 修复方向

### 方向 1（置信度: 高）— 在 CMake 配置后移除非架构兼容标志
SeisSol 上游的 `CMakeLists.txt` 或其子模块 CMake 脚本中硬编码了 `-mno-red-zone`（可能还有 `-mno-vzeroupper`）。在 Dockerfile 中 `cmake -B build` 之后、`cmake --build` 之前，需要用 `sed` 或 `find ... -exec sed` 对 `build/` 目录下生成的 `flags.make` 或相关 `CMakeCache.txt`/编译配置文件进行扫描，移除非当前架构支持的编译选项。或者直接在 SeisSol 源码目录中 patch 上游的 `CMakeLists.txt`，将 `-mno-red-zone` 包在 `if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|amd64")` 条件块中。

### 方向 2（置信度: 中）— 确认 SP3 的同版本 SeisSol 是否也包含此标志
若 SP3 构建成功而 SP4 失败，可能是 SP4 基础镜像的编译工具链（GCC 版本）对 `-mno-red-zone` 的处理行为与 SP3 不同（例如早期 GCC 版本对此标志仅警告而不报错）。需要对比两个 SP 版本基础镜像中的 GCC 版本差异，确认是否需要针对 SP4 做额外适配。

## 需要进一步确认的点
1. 需要确认 SeisSol 202103_Sumatra 源码中具体是哪个 CMakeLists.txt（或其子模块 Yateto/generated_code 的编译配置）注入了 `-mno-red-zone` 标志。
2. 需要确认 openEuler 24.03-LTS-SP3 的 aarch64 SeisSol 构建是否成功，以便判断该问题是 SP4 特有的工具链兼容性问题，还是全版本通用的架构兼容性问题。
3. 日志中还可能存在类似的 x86_64 专属标志（如 `-mno-vzeroupper`、`-mno-sse`、`-mno-mmx` 等），建议一并在 aarch64 环境下进行排查和处理。

## 修复验证要求
若采用方向 1 对 SeisSol 上游源码或生成文件进行正则 patch，code-fixer 必须：
1. 从 `https://github.com/SeisSol/SeisSol.git` 的 `202103_Sumatra` 分支确认 CMakeLists.txt 及其子模块（特别是 Yateto 代码生成模块）中定义 `-mno-red-zone` 的实际位置。
2. 在 aarch64 容器环境中执行 `cmake --build` 验证该标志已被正确移除或条件化，构建可完整通过。

# CI 失败分析报告

## 基本信息
- PR: #3033 — chore(seissol): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: aarch64编译标志不兼容
- 新模式症状关键词: `-mno-red-zone`, `unrecognized command-line option`, `aarch64`, `c++: error`, `SeisSol`

## 根因分析

### 直接错误
```
#14 55.53 c++: error: unrecognized command-line option '-mno-red-zone'
#14 55.53 gmake[2]: *** [CMakeFiles/SeisSol-lib.dir/build.make:358: CMakeFiles/SeisSol-lib.dir/src/generated_code/subroutine.cpp.o] Error 1
#14 83.94 gmake[1]: *** [CMakeFiles/Makefile2:100: CMakeFiles/SeisSol-lib.dir/all] Error 2
#14 83.94 gmake: *** [Makefile:91: all] Error 2
#14 ERROR: process "/bin/sh -c git clone --recursive --depth 1 --branch ${VERSION} https://github.com/SeisSol/SeisSol.git /tmp/seissol && ... cmake --build build --parallel $(nproc) && ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `HPC/seissol/202103.Sumatra/24.03-lts-sp4/Dockerfile:59`（SeisSol 编译步骤）
- 失败原因: SeisSol 构建系统（或其 CMake 配置文件）在 aarch64 平台上向 GCC 传入了 `-mno-red-zone` 编译标志。该标志是 x86_64 架构专用选项（禁用红区优化），在 aarch64 GCC 上不被识别，导致编译 `src/generated_code/subroutine.cpp.o` 时失败。

### 与 PR 变更的关联
- **直接关联**。PR 新增了 `HPC/seissol/202103.Sumatra/24.03-lts-sp4/Dockerfile`，该 Dockerfile 在 `RUN` 步骤中执行 SeisSol 源码编译。构建在 aarch64 架构上运行（日志中 ParMETIS 构建路径 `/tmp/parmetis/build/Linux-aarch64/libparmetis` 确认了架构）。
- Dockerfile 已设置 `-DHOST_ARCH=noarch` 企图禁用架构特定优化，但该 cmake 参数并未阻止 SeisSol 内部生成的源码文件（`subroutine.cpp`）或构建规则中引入 `-mno-red-zone` 标志。
- 该问题不出现在已有的 x86_64 构建中，也不出现在已有的 `24.03-lts-sp3` 版本中（如果其构建仅跑 x86_64 或已做相应处理）。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 SeisSol 编译步骤中，于 `cmake` 配置之前或编译过程中，通过 `sed` 或 `cmake` 参数剔除/遮蔽 `-mno-red-zone` 标志。具体做法：
- 定位 SeisSol 源码中何处引入了 `-mno-red-zone`（通常在 `CMakeLists.txt` 或 `cmake/` 目录下的工具链文件中），用 `sed` 在 `cmake -B build` 之前将该标志移除或替换为条件判断（`if(NOT CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64")`）。
- 或者在 cmake 配置时通过 `-DCMAKE_CXX_FLAGS` 追加 `-Wno-error` 来降级，但这不是根本方案。

### 方向 2（置信度: 高）
参考已有 `24.03-lts-sp3` Dockerfile 中是否对该问题做过处理，如果有，将其处理方式移植到新 Dockerfile 中。

## 需要进一步确认的点
1. 确认现有 `HPC/seissol/202103.Sumatra/24.03-lts-sp3/Dockerfile` 是否在 aarch64 上成功构建过，以及是否包含针对 `-mno-red-zone` 的处理逻辑。
2. 确认 SeisSol 源码（`202103_Sumatra` 分支）中 `-mno-red-zone` 标志具体在哪个 CMake 文件中设置，以便精确定位 sed 目标。
3. 确认 `-mno-red-zone` 标志来自 SeisSol 主仓库还是其 submodule（如 `Eigen`、`PUML`、`xdmfwriter`）。

## 修复验证要求
- code-fixer 在提交前必须验证修改后的 Dockerfile 在 aarch64 和 amd64 两个架构上均能成功构建。
- 由于涉及 `sed` 修改上游源码中的 CMake 文件，需确认 `sed` 表达式在目标文件中的命中次数和准确性，避免静默失败。

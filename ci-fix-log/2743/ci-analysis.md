# CI 失败分析报告

## 基本信息
- PR: #2743 — 【自动升级】seissol容器镜像升级至202103.Sumatra版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式 + 模式20（次要）
- 新模式标题: 上游源码缺失sched.h头文件
- 新模式症状关键词: cpu_set_t does not name a type, GCC 12, sched.h, Pin.h, SeisSol

## 根因分析

### 直接错误
```
#14 85.78 /tmp/seissol/src/Parallel/Pin.h:50:3: error: 'cpu_set_t' does not name a type
#14 85.78    50 |   cpu_set_t processMask{};
#14 85.78       |   ^~~~~~~~~
#14 85.78 /tmp/seissol/src/Parallel/Pin.h:51:3: error: 'cpu_set_t' does not name a type
#14 85.78    51 |   cpu_set_t openmpMask{};
#14 85.78 /tmp/seissol/src/Parallel/Pin.h:55:3: error: 'cpu_set_t' does not name a type
#14 85.78    55 |   cpu_set_t getProcessMask() const { return processMask; };
#14 85.78 /tmp/seissol/src/Parallel/Pin.h:56:3: error: 'cpu_set_t' does not name a type
#14 85.78    56 |   cpu_set_t getWorkerUnionMask() const;
#14 85.78 /tmp/seissol/src/Parallel/Pin.h:57:3: error: 'cpu_set_t' does not name a type
#14 85.78    57 |   cpu_set_t getFreeCPUsMask() const;
#14 85.78 /tmp/seissol/src/Parallel/Pin.h:58:33: error: 'cpu_set_t' has not been declared
#14 85.78 /tmp/seissol/src/Parallel/Pin.h:60:35: error: 'cpu_set_t' has not been declared
...
#14 85.97 gmake[2]: *** [CMakeFiles/SeisSol-lib.dir/build.make:579: CMakeFiles/SeisSol-lib.dir/src/Parallel/Pin.cpp.o] Error 1
#14 99.94 gmake[1]: *** [CMakeFiles/Makefile2:92: CMakeFiles/SeisSol-lib.dir/all] Error 2
#14 99.94 gmake: *** [Makefile:91: all] Error 2
#14 ERROR: process "/bin/sh -c git clone --recursive --depth 1 --branch ${VERSION} https://github.com/SeisSol/SeisSol.git /tmp/seissol && ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: 上游 SeisSol 源码 `/tmp/seissol/src/Parallel/Pin.h:50`
- 失败原因: SeisSol `v202103.Sumatra` 版本的 `src/Parallel/Pin.h` 使用了 POSIX 类型 `cpu_set_t`，但未显式 `#include <sched.h>`。在 GCC 12（openEuler 24.03-lts-sp3 搭载的编译器）上，`<sched.h>` 不再被其他头文件间接包含，导致 `cpu_set_t` 类型未声明，编译失败。

### 与 PR 变更的关联
PR 新增了 `HPC/seissol/202103.Sumatra/24.03-lts-sp3/Dockerfile`，该 Dockerfile 从 GitHub 克隆 SeisSol `v202103.Sumatra` 源码并在 openEuler 24.03 上编译。上游源码存在 GCC 12 兼容性问题（缺失 `<sched.h>` 显式包含），Dockerfile 中未施加补丁修复，导致构建失败。这个错误**与 PR 的改动直接相关**（新增的 Dockerfile 触发了上游 bug 的暴露），但**根本原因在上游源代码**。

**次要问题**：Dockerfile 第 97 行 `ENV LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 自引用了未定义变量，BuildKit 报告 `UndefinedVar` 警告（匹配**模式20**）。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `git clone` 后、`cmake` 前，用 `sed` 向 `src/Parallel/Pin.h` 添加 `#include <sched.h>`，解决 `cpu_set_t` 类型未声明问题。参考现有做法（如模式15、模式21 中的 sed patch），在 SeisSol build 步骤中加入一行 sed 命令。

### 方向 2（置信度: 高，次要）
将 Dockerfile 第 97 行 `ENV LD_LIBRARY_PATH=/usr/lib64/openmpi/lib:/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH` 中的 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`，消除 BuildKit `UndefinedVar` 警告。

## 需要进一步确认的点
1. 确认 SeisSol `v202103.Sumatra` 的 `src/Parallel/Pin.h` 是否确实缺少 `#include <sched.h>`（从日志上下文可高置信度推断，但 code-fixer 应在修复时验证上游仓库实际文件内容）。
2. CI 日志中的 cmake 命令包含 `-DCMAKE_CXX_FLAGS="-D_GNU_SOURCE"`，但 PR diff 的 Dockerfile 中不存在此参数——需确认是 CI 系统自动注入，还是 diff 与构建时的 Dockerfile 存在差异。此差异不影响根因判断。

## 修复验证要求
code-fixer 必须从 SeisSol v202103.Sumatra 的 `src/Parallel/Pin.h` 获取实际文件内容，确认 `cpu_set_t` 的使用位置及缺失的 `#include <sched.h>`，验证 sed 命令能正确在合适位置（如文件头部最后一个 `#include` 之后）插入该 include，然后再提交。

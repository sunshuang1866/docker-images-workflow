# 修复摘要

## 修复的问题
SeisSol `v202103_Sumatra` 源码编译时 `cpu_set_t` 类型未识别，在 GCC 12 + openEuler 24.03 环境下需要 `_GNU_SOURCE` 宏才能暴露该类型。

## 修改的文件
- `HPC/seissol/202103.Sumatra/24.03-lts-sp3/Dockerfile`: 在 SeisSol 的 cmake 配置步骤中添加 `-DCMAKE_CXX_FLAGS="-D_GNU_SOURCE"` 参数

## 修复逻辑
CI 分析报告指出根因是 `src/Parallel/Pin.h` 和 `Pin.cpp` 使用了 `cpu_set_t`（CPU 亲和性 API 类型），但编译时未定义 `_GNU_SOURCE`，导致该类型不可见。经上游仓库 `https://raw.githubusercontent.com/SeisSol/SeisSol/202103_Sumatra/src/Parallel/Pin.h` 和 `Pin.cpp` 验证确认：Pin.h 只包含 `<string>` 但直接使用 `cpu_set_t` 声明类成员和方法签名；Pin.cpp 虽包含 `<sched.h>`，但它将 `#include "Pin.h"` 放在 `<sched.h>` 之前，导致 Pin.h 被处理时 `cpu_set_t` 尚未声明。

采用分析报告中置信度最高的 Direction 1 修复方案：在 cmake 命令中追加 `-DCMAKE_CXX_FLAGS="-D_GNU_SOURCE"`，通过编译器宏定义使 `cpu_set_t` 在系统头文件中可见。此为最小侵入性修改，仅增加一行 cmake 参数，不改动上游源码结构。

已从上游 `202103_Sumatra` tag 获取 `Pin.h` 和 `Pin.cpp` 验证，确认问题与此修复匹配。

## 潜在风险
- `_GNU_SOURCE` 宏可能影响其他编译单元的 GNU 扩展行为（如 `O_CLOEXEC`、`strerror_r` 返回值等），但 SeisSol 本身已使用 GNU 扩展 API（`sched_getaffinity`、`CPU_ZERO` 等），因此该宏符合项目实际依赖，风险极低。
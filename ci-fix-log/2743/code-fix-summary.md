# 修复摘要

## 修复的问题
SeisSol `v202103.Sumatra` 上游源码 `src/Parallel/Pin.h` 使用了 `cpu_set_t` 类型但未显式包含 `<sched.h>`，在 GCC 12（openEuler 24.03-lts-sp3）上编译失败。

## 修改的文件
- `HPC/seissol/202103.Sumatra/24.03-lts-sp3/Dockerfile`: 在 `git clone` 后、`cmake` 前增加一行 `sed` 命令，向 `src/Parallel/Pin.h` 中插入 `#include <sched.h>`

## 修复逻辑
已从上游 `https://raw.githubusercontent.com/SeisSol/SeisSol/202103_Sumatra/src/Parallel/Pin.h` 获取实际文件内容验证，确认该文件仅 `#include <string>` 而无 `<sched.h>`，导致 `cpu_set_t` 类型在 GCC 12 上未声明。通过 `sed` 在 `#include <string>` 之后追加 `#include <sched.h>`，正则匹配成功。这是最小化修复，不改变其他构建逻辑。

次要问题（Dockerfile 第 97 行 `$LD_LIBRARY_PATH` 自引用）：实际文件中已使用 `${LD_LIBRARY_PATH:-}` 格式，无需修改。

## 潜在风险
- 该 `sed` 命令依赖 `#include <string>` 这一确切行存在。若上游未来版本修改了该行的 include 顺序或内容，sed 将无法匹配并导致构建失败（`sed` 不报错但不会插入）。当前针对 `202103_Sumatra` tag 锁定版本，风险可控。
- 该修复仅影响 `cpu_set_t` 的声明问题，不涉及任何运行时行为变更。
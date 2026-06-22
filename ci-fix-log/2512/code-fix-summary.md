# 修复摘要

## 修复的问题
Dockerfile 中 clang 运行时库符号链接硬编码了 `aarch64` 架构路径，导致 x86_64 构建时找不到正确的库文件。将其改为根据容器实际架构（`uname -m`）动态选择路径。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 在构建 RUN 中新增架构感知的 clang library 符号链接逻辑（第 34-39 行），用 `ARCH=$(uname -m)` 替代硬编码的 `aarch64`。

## 修复逻辑
CI 分析报告指出以下三个问题及其修复状态：

1. **方向 1 — FoundationDB RPM 架构硬编码**：已在先前提交（`beb06627`）中通过多阶段构建修复，用 `COPY --from=fdb` 替代 RPM 安装，消除了架构依赖。

2. **方向 2 — Clang library 符号链接路径硬编码**（本次修复）：先前提交在修复方向 1 时将 clang library 符号链接整个移除。本次修复将其重新加入，并使用 `ARCH=$(uname -m)` 动态获取当前容器架构：
   - x86_64 上路径为 `/usr/lib/clang/17/lib/x86_64-openEuler-linux-gnu/`
   - aarch64 上路径为 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/`
   
   符号链接创建在 `mkdir -p /usr/lib64/clang/17/lib/linux` 目录下，使 linker 能在统一路径找到 clang 运行时库（如 `libclang_rt.builtins-${ARCH}.a`）。glob 匹配失败时（路径不存在）`for` 循环静默跳过，不会中断构建。

3. **方向 3 — Git shallow clone 不兼容**：已在先前提交中修复，移除了 `--depth 1` 参数。

## 潜在风险
- 若 openEuler 未来版本中 clang 版本号变更（非 17），`/usr/lib/clang/17/lib/` 路径将失效，符号链接 step 会静默跳过（glob 无匹配），可能导致后续 cmake 构建因找不到 clang runtime 库而失败。
- 若 openEuler 改变 library 子目录命名规则（非 `${ARCH}-openEuler-linux-gnu`），同样会导致 glob 不匹配。
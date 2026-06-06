# 修复摘要

## 修复的问题
在 vllm-cpu 0.22.1 Dockerfile 中缺失 AVX512BF16 fallback patch，导致无 AVX512BF16 指令集的 x86_64 平台编译 `mla_decode.cpp` 时 `KernelVecType<c10::BFloat16>` 解析为 `void` 从而编译失败。

## 修改的文件
- `AI/vllm-cpu/0.22.1/24.03-lts-sp3/Dockerfile`: 在 `git clone` 与 `pip install` 之间插入对 `csrc/cpu/mla_decode.cpp` 的 patch 步骤（backport vllm-project/vllm PR #34052），将 s390x/aarch64 特定的 `#elif` 分支合并为通用 `#else` fallback 分支。

## 修复逻辑
CI 分析报告指出失败模式符合知识库模式15：x86_64 构建失败而 aarch64 成功，特征与 AVX512BF16 编译错误完全吻合。v0.16.0 版本的 Dockerfile 包含该 patch 且构建成功，v0.22.1 新 Dockerfile 遗漏了此 patch。修复方式是从 v0.16.0 Dockerfile 复制相同的 `python3 -c` patch 命令，插入到相同的逻辑位置（`git clone` 之后、`pip install` 之前）。

## 潜在风险
- vllm 0.22.1 中 `csrc/cpu/mla_decode.cpp` 的文件路径或代码模式可能与 v0.16.0 不同，导致 patch 字符串匹配失败，`python3 -c` 命令将报错。但由于 x86_64 构建日志缺失，无法提前验证，这是基于现有证据的最优修复。
- 如果 v0.22.1 上游已合入等效修复，则此 patch 可能无害（`str.replace` 匹配不到旧字符串时不修改文件）。
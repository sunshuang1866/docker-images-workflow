# 修复摘要

## 修复的问题
vllm-cpu 0.23.0 编译时 `-j=8` 并行编译导致 OOM，`cc1plus` 被 Linux OOM Killer 杀死。

## 修改的文件
- `AI/vllm-cpu/0.23.0/24.03-lts-sp3/Dockerfile`: 在第 41 行 `setup.py bdist_wheel` 命令前添加 `MAX_JOBS=4` 环境变量，将 cmake/ninja 并行编译数从默认 8 降至 4。

## 修复逻辑
根据 CI 分析报告，根因是 `setup.py` 内部调用 cmake 构建时默认使用 `-j=8` 并行编译，编译 `cpu_attn.cpp` 等重量级模板代码时内存消耗过大，触发 OOM Killer。`MAX_JOBS` 是 pytorch/setuptools 扩展通用的并行度控制环境变量，设置此变量后 cmake 构建会使用指定值替代默认的并行数，从而降低峰值内存占用，避免 OOM。

## 潜在风险
- 编译时间可能略有增加（约 1.5-2x），但可避免 OOM 导致构建失败。
- 如果 CI 节点内存仍然不足，可能需要进一步降低至 `MAX_JOBS=2`。
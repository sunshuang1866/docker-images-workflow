# 修复摘要

## 修复的问题
CI 基础设施故障：`pip3 install sglang` 下载依赖包 `nvidia-cusparse` 时因网络中断导致 `IncompleteRead` / `ProtocolError` 异常，属于瞬时网络故障，非代码缺陷。

## 修改的文件
无。此失败为 `infra-error`，与 PR 代码逻辑无关。

## 修复逻辑
CI 构建环境中从 PyPI 下载大体积 CUDA 相关 Python 包（`nvidia-cusparse` 145.9 MB）时网络连接中断，导致构建失败。这是瞬时网络波动问题，重新触发 CI 构建即可通过。根据规范，`infra-error` 类型的失败不应强行修改代码。

## 潜在风险
无。
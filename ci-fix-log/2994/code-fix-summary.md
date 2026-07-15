# 修复摘要

## 修复的问题
CI 构建失败为 infra-error，非代码问题，无需修改源码。

## 修改的文件
无。本次 CI 失败由 BuildKit 构建器在 dnf 下载仓库元数据阶段被优雅终止导致（`graceful_stop`），与 PR 代码变更无关。

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型为 `infra-error`
- 构建在第 #7 步（`dnf install` 下载阶段）即被中断，尚未执行到步骤 #8（编译 Python）和步骤 #9（pip install scann），因此无法评估 Dockerfile 内容是否正确
- `graceful_stop` debug 信息表明这是构建器的主动/被动资源回收行为（如超时、节点下线、资源配额耗尽），与 PR 代码内容无关
- 建议重新触发 CI 构建

按照指令要求，`infra-error` 不进行代码修改。

## 潜在风险
无
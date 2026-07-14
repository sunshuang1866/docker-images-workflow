# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error）：Docker BuildKit 构建器节点在 `dnf install` 下载系统元数据阶段被异常终止（`graceful_stop`），与 PR 代码变更无关。

## 修改的文件
无（infra-error，无代码变更需要）

## 修复逻辑
CI 失败分析报告明确指出该失败类型为 `infra-error`，根因是 Docker BuildKit 构建器实例被外部信号关闭（`graceful_stop`）。失败发生在 `dnf install` 下载 openEuler 官方仓库元数据阶段（dnf 下载速度仅 77 kB/s），尚未执行到 PR 新增的 Python 编译或 pip 安装步骤。PR 仅新增 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据，这些文件本身正确无误。

**解决方案：重新触发 CI 构建即可，大概率通过。**

## 潜在风险
无。若重试后仍失败，需联系 CI 运维团队排查构建节点健康状态或网络配置。
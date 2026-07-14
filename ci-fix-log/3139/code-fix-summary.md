# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。

## 修改的文件
无。

## 修复逻辑
CI 失败分析报告判定此次失败为 **infra-error**。根因是 `pip install` 从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13`（366.2 MB 大文件）时发生 TCP 读超时（`ReadTimeoutError`），导致 Docker 构建退出码 2。该失败与 PR #3139 的代码变更（新增 openEuler 24.03-LTS-SP4 的 Dockerfile 及配套文件）无关，属于 CI 构建环境的网络波动问题。

按照修复原则，infra-error 不应强行修改代码。建议措施：
- 重试 CI 构建（网络波动可能是临时的）
- 或更换 PyPI 镜像源为更稳定的地址（如 `pypi.tuna.tsinghua.edu.cn`）
- 或通过 `PIP_DEFAULT_TIMEOUT` 环境变量增大 pip 下载超时阈值

## 潜在风险
无。
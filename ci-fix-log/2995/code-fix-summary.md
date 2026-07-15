# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），与 PR #2995 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认此失败为 **infra-error**：
- Docker 镜像的构建（`#7 DONE 199.0s`）和推送（`[Build] finished`, `[Push] finished`）全部成功。
- 失败仅发生在 CI 后置测试阶段 `[Check]`，根因是 `eulerpublisher` 包中自带的 `bwa_test.sh` 脚本使用 Windows CRLF 换行符，导致 shebang `#!/bin/sh` 被解析为 `#!/bin/sh\r`，内核找不到 `/bin/sh\r` 解释器。
- 该脚本位于 CI 工具链的 pip 安装路径下（`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`），不在 PR 仓库中，不由任何 PR diff 引入。
- 根据规则：infra-error 无需修改源代码，不应强行改代码。

需联系 CI 平台维护者修复 `eulerpublisher` 包中 `bwa_test.sh` 的 CRLF 行尾问题，或检查 CI runner 的 Git `core.autocrlf` 配置。

## 潜在风险
无（无需代码修改）
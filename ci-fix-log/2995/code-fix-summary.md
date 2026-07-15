# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：`eulerpublisher` 包中的 `bwa_test.sh` 测试脚本使用 CRLF 行尾，导致 shebang 行被错误解析为 `/bin/sh\r`，操作系统无法找到该解释器而报 `bad interpreter`。**与 PR 代码变更无关，无需修改 PR 文件。**

## 修改的文件
无。此为 CI 基础设施问题，不需要修改 PR 仓库中的任何源代码文件。

## 修复逻辑
1. PR #2995 的 Dockerfile 构建过程完全成功——依赖安装、源码下载、编译、镜像构建和推送均正常完成。
2. 唯一失败发生在 CI 后置验证 [Check] 阶段，CI 工具 `eulerpublisher` 尝试运行 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 时，因该测试脚本自身文件格式问题（CRLF 行尾）无法被执行。
3. 该测试脚本属于 `eulerpublisher` Python 包的 `/etc/` 目录，是 CI 基础设施的一部分，不属于此次 PR 新增或修改的文件。
4. 修复应由 CI 运维人员在 `eulerpublisher` 包中将 `bwa_test.sh` 的行尾从 CRLF 转换为 LF（可用 `dos2unix` 或在打包/部署流程中增加行尾规范化步骤）。

## 潜在风险
无。不需要对源码仓库做任何修改，不存在引入新问题的风险。
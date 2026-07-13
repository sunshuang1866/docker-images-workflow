# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：CI runner 上缺少 `shunit2` shell 测试框架，导致镜像构建成功后的 Check 验证阶段失败。与 PR #2900 的代码改动无关，无需修改任何源代码。

## 修改的文件
无。此为 CI 基础设施问题，不属于代码层面的缺陷。

## 修复逻辑
CI 分析报告确认：
- Docker 镜像构建阶段（#1-#14）全部成功，镜像已构建并推送至 registry。
- 失败发生在构建完成后的 `[Check]` 阶段，由 `eulerpublisher` 工具调用 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`，该脚本尝试引入 `shunit2` 但框架未在 runner 上安装。
- 本次 PR 仅新增 httpd 镜像的 Dockerfile、启动脚本及文档/元数据文件，与 CI 检查基础设施无任何关联。

**修复方向**（需 CI 运维人员处理）：
1. 在执行检查任务的 CI runner 上安装 `shunit2`（可从 EPEL 仓库或 GitHub `kward/shunit2` 获取）。
2. 或者检查 `common_funs.sh` 中 `shunit2` 的引用路径是否正确，确保 `shunit2` 所在目录在 `PATH` 中。

## 潜在风险
无。不涉及代码修改，不存在引入新问题的风险。
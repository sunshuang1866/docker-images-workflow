# 修复摘要

## 修复的问题
CI 基础设施错误：`shunit2` Shell 测试框架未安装在 CI runner 环境中，导致 Check 阶段崩溃。与 PR #2900 的代码变更无关，无需修改任何源代码文件。

## 修改的文件
无（infra-error，不需要代码修改）

## 修复逻辑
CI 失败分析报告确认：
- Docker 构建（`./configure && make && make install`）全程顺利完成
- 镜像导出和推送成功（`[Build] finished`, `[Push] finished`）
- 失败发生在 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`，即 CI runner 系统路径下的 `common_funs.sh` 脚本执行 `. shunit2`（source 命令）时找不到 `shunit2`
- PR 仅新增 Dockerfile、启动脚本、README/yml 条目，均为镜像定义层变更，未触及任何 CI 流水线配置或测试脚本
- 这是 CI 基础设施层面的问题，需要 CI 运维人员在 runner 环境中安装 `shunit2`（如 `dnf install shunit2`）

## 潜在风险
无
# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 测试脚本 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI Runner 上缺少 `shunit2`（Shell 单元测试框架），导致 [Check] 阶段的容器验证测试脚本无法执行，所有 Check Items 结果均为空，最终判定测试失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。Docker 镜像构建和推送均已成功完成（日志中明确显示 `[Build] finished` 和 `[Push] finished`，镜像已成功推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`）。失败仅发生在 CI Runner 自身的测试套件环境——`shunit2` 工具未安装，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 节点上安装 `shunit2` 测试框架。可以检查 CI Runner 的置备脚本/Ansible playbook，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能够成功 source `shunit2`（常见安装方式：`dnf install shunit2` 或从 GitHub 克隆 `kward/shunit2` 到指定路径）。修复后重新触发 CI 即可通过 [Check] 阶段。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 上的正确安装方式（RPM 包名或 source 路径）。
- 确认 CI Runner 节点上 `common_funs.sh` 期望的 `shunit2` 安装路径，以便正确配置。
- 后续可关注 Docker 构建过程中的 2 个 `LegacyKeyValueFormat` 警告（Dockerfile 第 26、30 行 ENV 使用旧格式），属于代码风格问题，不影响构建。

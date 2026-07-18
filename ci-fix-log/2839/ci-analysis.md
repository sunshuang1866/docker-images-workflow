# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI runner 上的测试脚本）
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架工具，导致 `eulerpublisher` 的 `[Check]` 阶段在发现镜像后无法执行容器验收测试。Docker 镜像构建和推送本身均已成功完成（日志中明确显示 `[Build] finished`、`[Push] finished`、Docker 阶段 `#8 DONE 268.4s`、`#11 DONE 58.0s`），失败仅发生在测试框架加载阶段。

### 与 PR 变更的关联
与 PR 变更无关。PR 仅新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh 及对应的 README.md 和 meta.yml 条目。Docker 构建阶段完全通过，失败原因为 CI runner 环境缺少 `shunit2` 测试框架，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 低）
在 CI runner 环境中安装 `shunit2` 工具（如在 runner 初始化脚本中添加 `dnf install shunit2 -y` 或 `pip install shunit2`），使 `[Check]` 阶段的容器验收测试能够正常执行。此修复需由 CI 运维团队处理，不涉及 PR 代码变更。

## 需要进一步确认的点
1. 需要确认 CI runner 上是否应该预装 `shunit2`，以及该 runner 此前执行其他 PR 的 Check 阶段是否正常（是否存在本次 runner 配置变更或镜像回退导致 shunit2 缺失）。
2. 由于 `shunit2` 缺失导致 Check 阶段在测试脚本加载时即崩溃（无法进入实际测试），无法确认容器镜像本身是否存在运行时问题。需要等 shunit2 修复后重新触发 CI，获取完整的 Check 测试结果后才能确定镜像是否真正可用。
3. 日志中出现 2 个 BuildKit 警告（`LegacyKeyValueFormat`，Dockerfile 第 26 和 30 行的 `ENV` 语句使用了旧版格式），这些警告不会导致构建失败，但可在后续优化。

## 修复验证要求
无需 code-fixer 介入。此失败属于 CI 基础设施问题（`infra-error`），PR 的 Dockerfile 代码本身无需修改。待 CI 运维团队修复 runner 环境后，重新触发 CI 流水线即可。

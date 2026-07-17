# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI缺少shunit2测试框架
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

Check 结果表格为空（无任何测试执行）：
```
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 环境中缺少 `shunit2` shell 测试框架，`common_funs.sh` 在 source `shunit2` 时失败，导致 [Check] 阶段完全无法执行任何容器验证测试。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 证据如下：
1. Docker 镜像构建阶段全部成功——所有 7 个 RUN 步骤均以 `DONE` 完成，镜像构建和推送均正常（`[Build] finished`、`[Push] finished`）。
2. PR 仅新增了 Dockerfile（httpd 2.4.66 on openEuler 24.03-lts-sp4）、httpd-foreground 脚本、并更新了 README.md、image-info.yml、meta.yml。这些变更均通过了构建阶段的验证。
3. 失败发生在 CI 平台的 [Check] 阶段，该阶段由 `eulerpublisher` 工具调用 `common_funs.sh` 脚本，而该脚本依赖的 `shunit2` shell 测试框架在 CI runner 上缺失——这是 CI 基础设施层面问题，与本次 PR 的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
CI 平台管理员需在 `eulerpublisher` 测试环境的 runner 上安装 `shunit2` shell 测试框架，确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 能够正常 source 到该库。此问题应在 CI 基础设施层面修复。

### 方向 2（置信度: 低）
如果 CI runner 环境无法及时修复，可尝试检查该 httpd 镜像是否有同级目录下其他已通过 Check 的同类型镜像（如 `2.4.66/24.03-lts-sp2/`），确认其 Check 流程是否正常。若非此 PR 独有问题（即同类镜像均无法通过 Check），则可直接判定为基础设施故障，与 PR 无关。

## 需要进一步确认的点
1. 同一 CI runner 上是否有其他镜像（如同项目的其他 PR）在 [Check] 阶段也因 `shunit2: file not found` 失败？如果是，则确认为 CI 平台层面的基础设施问题。
2. `shunit2` 是否曾在该 CI runner 上可用、后因环境变更被移除？需与 CI 运维人员确认。
3. 日志中出现的 `LegacyKeyValueFormat` Docker 警告（`ENV key value` 应改为 `ENV key=value`）是**非致命**的构建建议，与本次失败无关，可忽略。

## 修复验证要求
此失败为 infra-error，Code Fixer 无需处理代码变更。若 CI 平台修复 `shunit2` 依赖后重新触发构建仍有问题，再根据新的 Check 日志进行分析。

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"相似但具体缺失依赖不同）
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: `shunit2: file not found, common_funs.sh, [Check] test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 宿主环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境中缺少 `shunit2` shell 单元测试框架，`eulerpublisher` 工具在 [Check] 阶段执行 `common_funs.sh` 时尝试 `. source shunit2` 失败，导致所有镜像健康检查测试无法运行，直接返回 `[Check] test failed`

### 与 PR 变更的关联
**与 PR 代码变更无关**。Docker 镜像构建全部 7 步骤均成功执行（`#10 DONE 41.6s`、`#11 DONE 0.1s` 等），Build 和 Push 阶段均正常完成（日志中 `[Build] finished`、`[Push] finished`）。失败仅发生在 CI 编排工具 `eulerpublisher` 的 [Check] 后处理阶段——该阶段因测试框架 `shunit2` 缺失而无法运行，属 CI 基础设施问题。

PR 新增的 Dockerfile 本身构建产物已验证：镜像 `2.4.66-oe2403sp4-x86_64` 已成功构建并推送至 registry（sha256:b38237a...）。日志中唯一的 warning（`LegacyKeyValueFormat`）是 Docker BuildKit 的格式建议，并非错误。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 的运行环境上安装 `shunit2` 包（openEuler 中可通过 `dnf install shunit2` 安装），使 `eulerpublisher` 的 Check 阶段的 `common_funs.sh` 能正常加载该测试框架。此修复无需修改任何 PR 代码。

## 需要进一步确认的点
1. 确认 CI Runner 宿主机上 `shunit2` 是否被意外卸载或从未安装——可检查同 PR 的其他架构构建 job（如 aarch64）是否也报了同样的 `shunit2: file not found` 错误
2. 确认 `eulerpublisher` 包是否将 `shunit2` 列为依赖但未正确声明，导致安装时遗漏
3. 确认该 CI Runner 节点是否正确配置了 `eulerpublisher` 测试套件的完整运行时依赖

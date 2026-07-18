# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 检查缺少 shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 的 [Check] 阶段执行容器镜像测试时，测试框架 `shunit2`（Shell 单元测试工具）在 CI runner 环境中不存在，导致测试脚本无法加载该工具，测试提前终止，检查结果表为空。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 和 entrypoint.sh 构建完全成功：
- Docker build 全部步骤通过（`#8 DONE 268.4s`，PostgreSQL 17.6 编译安装完成）
- 镜像导出和推送成功（`#11 DONE 58.0s`）
- `[Build] finished` 和 `[Push] finished` 均正常

失败纯属 CI 基础设施问题：eulerpublisher 的 `[Check]` 阶段依赖 `shunit2` 工具，而该工具未安装在当前 CI runner 上。这是 `infra-error`，Code Fixer 无需对 Dockerfile 或 PR 代码做任何修改。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 镜像或 eulerpublisher 测试环境中安装 `shunit2` 工具。openEuler 上可通过 `dnf install shunit2` 安装，或从 GitHub 拉取 shunit2 源码部署到 `/usr/local/etc/eulerpublisher/tests/` 路径下。此修复属于 CI 平台运维范畴，不涉及 PR 代码变更。

## 需要进一步确认的点
- `shunit2` 是否在 openEuler 24.03-LTS-SP4 的软件源中可用（`dnf search shunit2`）
- 若不可用，需确认 eulerpublisher 期望的 shunit2 安装路径和版本
- 该 CI runner 是否只影响 `postgres` 镜像的 [Check] 阶段，还是所有镜像的 [Check] 均因此失败（可通过查看其他成功/失败的 CI job 对比确认）

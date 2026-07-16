# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, eulerpublisher, Check test failed, common_funs.sh

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
- 失败位置: `eulerpublisher` CI 测试框架的 `common_funs.sh:13`（Check 阶段）
- 失败原因: CI runner 环境中缺少 `shunit2` 单元测试框架，导致 `eulerpublisher` 在镜像检查（[Check]）阶段无法执行测试校验脚本。Docker 镜像的构建和推送均已成功完成（`[Build] finished`、`[Push] finished`），仅 Check 步骤因 CI 基础设施问题而失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，Docker 构建阶段（#8）全部编译链接步骤均正常通过，镜像导出和推送（#11）也成功完成。失败完全发生在 `eulerpublisher` 测试框架执行 `common_funs.sh` 时，因 CI runner 未安装 `shunit2` 而中断。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` 包。需要在 CI runner 上安装 `shunit2`（openEuler 上可通过 `dnf install shunit2` 安装），或确保 `eulerpublisher` 的依赖项在 CI 环境中完整。此问题属于 CI 基础设施配置问题，Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- 该 Check 阶段的失败是否在所有 openEuler 24.03-LTS-SP4 CI runner 上都复现（即 `shunit2` 是否普遍缺失），还是仅限当前 runner（如 `ecs-build-docker-x86-64-01-sp` 等特定节点）
- `shunit2` 在 openEuler 24.03-LTS-SP4 仓库中的确切包名（可能为 `shunit2` 或 `shUnit2`）
- 是否需要同时检查同批次其他镜像的 Check 阶段是否也受此影响（排除单点问题）

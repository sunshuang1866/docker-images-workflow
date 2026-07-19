# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺少shunit2
- 新模式症状关键词: `shunit2: No such file or directory`, `[Check] test failed`, `common_funs.sh`

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 上 `eulerpublisher` 工具的容器测试框架（[Check] 阶段）依赖 `shunit2` shell 单元测试库，但 `shunit2` 未安装在 Runner 环境中，导致测试脚本 `common_funs.sh` 在第 13 行尝试引入 `shunit2` 时失败。Docker 镜像的构建和推送阶段均正常完成（`[Build] finished`, `[Push] finished`）。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 PostgreSQL 17.6 Dockerfile 和 entrypoint.sh 在构建阶段编译成功（`#8 DONE 268.4s`），镜像成功推送（`#11 DONE 58.0s`）。失败发生在 CI 基础设施层的 `eulerpublisher` [Check] 测试阶段，因 Runner 缺少 `shunit2` 依赖导致所有容器检查项均未执行（检查结果表为空）。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员需要在 Runner 环境中安装 `shunit2` 包。`shunit2` 是 bash shell 单元测试框架，应在 CI Runner 的测试环境中预装，或者由 `eulerpublisher` 工具在安装时声明为依赖自动拉取。该问题与 PR 代码无关，Code Fixer 无需对 Dockerfile 或 entrypoint.sh 做任何修改。

## 需要进一步确认的点
- 确认 `shunit2` 在 CI Runner 上的预期安装方式（yum/dnf 包 `shunit2` 或手动部署脚本）。
- 确认该 Runner 上其他 PR 的 [Check] 阶段是否也因同样原因失败（若为全局性问题，则确认为纯 infra 问题；若仅该 PR 失败，需排查调度差异）。

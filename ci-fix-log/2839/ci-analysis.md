# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 后置验证阶段（`[Check]`）中，shell 测试框架 `shunit2` 在 CI runner 环境中不可用（`No such file or directory`），导致 `eulerpublisher` 的测试套件无法启动，`[Check]` 步骤直接崩溃并上报 CRITICAL 级别失败。Docker 镜像的构建（`[Build]`）和推送（`[Push]`）阶段均成功完成。

### 与 PR 变更的关联
与 PR 变更**无关**。该 PR 仅新增了一个 Postgres 17.6 的 Dockerfile、entrypoint.sh、更新了 README.md 和 meta.yml。Docker 镜像构建成功（`#8 DONE 268.4s`）、推送成功（`[Push] finished`），失败完全发生在 CI 基础设施的 `[Check]` 后置验证阶段，因测试框架 `shunit2` 未安装在 runner 上而崩溃。Check 结果表为空（没有任何测试条目被加载），进一步证实没有测试实际运行，属于 CI 基础设施环境问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架，或确保 `eulerpublisher` 测试套件在所需依赖就绪的环境下运行。这不是 Dockerfile 或代码层面的问题，Code Fixer 无需处理。

## 需要进一步确认的点
- 同一 runner 上其他成功构建的 PR 是否也使用 `[Check]` 步骤并正常通过了 shunit2 测试（以确认是否为本 PR 专属的 runner 配置问题，还是全局 CI 环境变更所致）
- `shunit2` 在此 CI 环境中预期由哪个包管理器安装（`dnf` / `pip` / 手动部署），以及该 runner 上 `shunit2` 所在的实际路径

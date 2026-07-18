# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 基础设施代码，非 PR 代码）
- 失败原因: CI runner 环境中缺少 `shunit2`（Bash 单元测试框架），导致 `common_funs.sh` 的 `source`/加载失败，[Check] 阶段的所有镜像测试用例均无法执行，测试结果表为空。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 的 Dockerfile、entrypoint.sh 及元数据更新。Docker 构建和推送阶段均已成功完成（`#8 DONE 268.4s`，`[Build] finished`，`[Push] finished`，镜像已成功推送到注册表 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`）。失败发生在 CI 流水线的 [Check] 阶段，该阶段需要 `shunit2` 框架来执行镜像测试用例，而该框架在当前 CI runner 上不存在。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包（可通过 `dnf install shunit2` 或从 GitHub releases 获取）。这是 CI 基础设施问题，Code Fixer 无需处理此 PR 的代码。

## 需要进一步确认的点
- 确认 CI runner 的操作系统版本及 `shunit2` 是否在其默认软件源中（openEuler 24.03-LTS-SP4 的 EPOL 源可能包含该包）。
- 确认该 CI runner 的 [Check] 阶段是否在所有 PR 上都报同样的错误，以排除个别 runner 的环境漂移。
- 如果 `shunit2` 已安装但路径不在 `PATH` 中，需检查 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13` 中的 `shunit2` source 路径是否正确。

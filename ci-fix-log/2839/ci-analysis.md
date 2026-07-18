# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`:13
- 失败原因: CI 测试框架 `eulerpublisher` 的 `common_funs.sh` 在第 13 行引用了 `shunit2`（一个 Shell 单元测试框架），但该依赖未安装在 CI Runner 环境中，导致 [Check] 阶段测试脚本无法执行。

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 新增 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，Docker 镜像的编译和推送阶段均已完成且成功（`#8 DONE 268.4s`、`#11 DONE 58.0s`、`[Build] finished`、`[Push] finished`）。失败发生在构建完成后的 CI [Check] 测试阶段，根因为 CI Runner 缺少 `shunit2` 测试框架依赖，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2`。对于基于 RPM 的 openEuler 环境，可通过 `dnf install shunit2` 或从 GitHub 获取 `shunit2` 脚本并放入 `PATH`（如 `/usr/local/bin/`）。该修复属于 CI 运维操作，不涉及 Dockerfile 或 PR 代码变更。

## 需要进一步确认的点
- 确认 `shunit2` 是否在 openEuler 24.03-LTS-SP4 的 RPM 仓库中可用（包名可能为 `shunit2`），或需要通过 `git clone` / `wget` 手动安装。
- 确认 CI Runner 镜像中 `shunit2` 的安装路径是否与 `common_funs.sh` 中的引用路径一致（当前通过 `source` 或 `PATH` 查找）。

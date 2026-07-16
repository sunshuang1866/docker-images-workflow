# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `Check test failed`

## 根因分析

### 直接错误
```
#14 DONE 31.3s
euler_builder_20260710_091535 removed
2026-07-10 09:18:18,406 - INFO - [Build] finished
2026-07-10 09:18:18,406 - INFO - [Push] finished
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 加载 `shunit2` shell 单元测试框架，但该框架在 CI runner 上未安装或不在 `PATH` 中，导致测试无法初始化即失败。Docker 镜像的构建（所有 7 个 Dockerfile 步骤均成功）和推送均已完成，失败仅限于 CI 测试基础设施层面。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、httpd-foreground 脚本、meta.yml/README.md/image-info.yml 条目。Docker 镜像构建和推送全程成功，`[Build] finished` 和 `[Push] finished` 日志明确证实镜像制品本身无问题。失败发生在 CI 的 [Check] 阶段，原因是 CI runner 缺少 `shunit2` 测试框架——这是 CI 基础设施的环境问题，非 PR 代码引入。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。该框架是 Shell 测试工具，需通过系统包管理器（如 `dnf install shunit2` 或 `pip install shunit2`）安装到 CI 构建节点的 `PATH` 中，使 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 能正确加载。此为 CI 基础设施变更，Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- 确认 CI runner 镜像/环境中是否应预装 `shunit2`。若 `shunit2` 是 `eulerpublisher` 测试框架的依赖，需在 CI 节点初始化脚本中补充安装。
- 确认该 CI runner（`ecs-build-docker-aarch64-01-sp` 或对应 x86_64 节点）在本次运行前是否发生过环境变更（如系统更新导致包被移除）。
- 若该问题在多个 PR 的 [Check] 阶段出现，说明是系统性的 CI 环境问题；若仅此 PR 出现，需排查该 job 的 runner 分配策略。

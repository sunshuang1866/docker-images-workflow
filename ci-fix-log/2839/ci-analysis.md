# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: (无)
- 新模式症状关键词: (无)

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
- 失败位置: CI Runner 测试环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2` Shell 单元测试框架，导致 [Check] 阶段无法加载测试工具，容器测试完全无法执行。Docker 镜像的构建和推送阶段均已成功完成（`#8 DONE 268.4s`、`[Build] finished`、`[Push] finished`）。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 新增的 Dockerfile 已正确完成编译构建和推送，PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上成功通过 `./configure && make -j "$(nproc)" && make install` 全部流程。失败发生在 CI 后置的容器静态检查阶段，属于 CI Runner 环境问题——测试框架 `shunit2` 未安装在 Runner 上。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` Shell 测试框架。`shunit2` 是容器测试脚本 `common_funs.sh` 的核心依赖，缺失导致所有容器镜像的 [Check] 阶段均无法执行。通常通过系统的包管理器安装（如 `dnf install shunit2` 或 `pip install shunit2`），或由 CI 初始化脚本自动部署。

## 需要进一步确认的点
- 确认 `shunit2` 在该 CI Runner 上是原本就缺失，还是近期被误删/环境变更导致
- 确认同 Runner 上其他镜像 PR 的 [Check] 阶段是否同样失败（如果是，则为 Runner 级系统性基础设施问题）

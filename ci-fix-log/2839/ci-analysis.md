# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, [Check] test failed

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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 `[Check]` 阶段的容器校验测试时，`common_funs.sh` 脚本尝试 source `shunit2` 单元测试框架，但该工具未安装或不在 `PATH` 中，导致所有测试用例无法执行。

### 与 PR 变更的关联
**与 PR 代码变更无关。** Docker 镜像构建（`#8 DONE 268.4s`）和推送到仓库（`#11 DONE 58.0s`）均成功完成。日志中 `[Build] finished` 和 `[Push] finished` 均正常。失败发生在 CI 编排层的 `[Check]` 阶段——这是 CI Runner 宿主环境缺少 `shunit2` 导致的测试框架运行失败，并非容器镜像构建或功能问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 宿主环境安装 `shunit2` 单元测试框架，确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 的 `source shunit2` 语句能正确找到该工具。这不是代码修复问题，而是 CI 基础设施配置问题。

## 需要进一步确认的点
1. 是否同一 CI Runner（`ecs-build-docker-x86-64` 系列）上最近有其他同类 PR（如其他 postgres 版本或同 OS 版本的应用镜像）在 `[Check]` 阶段也出现了相同错误？如果多 PR 同时受影响，可确认是 Runner 环境全局问题。
2. `shunit2` 是否曾经存在于该 CI 环境中，后因 Runner 镜像更新或清理操作被移除？
3. 是否存在一个 CI 前置脚本负责安装 `shunit2`，但该脚本在本次运行中未被正确执行？

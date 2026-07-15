# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, check test failed, common_funs.sh

## 根因分析

### 直接错误
```
2026-07-09 09:40:23,529 - INFO - [Build] finished
2026-07-09 09:40:23,529 - INFO - [Push] finished
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
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
- 失败原因: CI 的 `[Check]` 阶段执行容器镜像测试脚本 `common_funs.sh` 时，第 13 行尝试加载 `shunit2`（Shell 单元测试框架），但该工具在 CI runner 上不存在（`No such file or directory`），导致测试无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（`[Build]`）和推送（`[Push]`）均成功完成（`#8 DONE 268.4s`，镜像 sha256 已生成并推送）。失败仅发生在 CI 编排工具 `eulerpublisher` 的 `[Check]` 阶段，因 runner 环境缺少 `shunit2` 测试框架导致测试脚本无法运行。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。该工具需要被放置在 `common_funs.sh` 可访问的路径下（或位于 `PATH` 中）。这属于 CI 基础设施配置问题，不涉及 PR 代码修改。

## 需要进一步确认的点
1. `shunit2` 是否在 CI runner 的镜像模板中预装，还是需要在此 job 中单独安装。
2. 同仓库的其他 openEuler 24.03-LTS-SP4 镜像（如已有类似 `Check` 测试流程的其他镜像）是否也遇到同样的 `shunit2` 缺失问题。
3. 该 CI runner 上 `common_funs.sh` 被调用的路径（`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`）下 `shunit2` 的预期安装位置是什么。

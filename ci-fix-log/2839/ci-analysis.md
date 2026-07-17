# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2未安装
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI Runner 的 `eulerpublisher` 测试框架依赖 `shunit2`（Shell 单元测试库），但该依赖在 CI 执行节点上未安装或不在 `PATH` 中，导致 `common_funs.sh` 无法 source `shunit2`，[Check] 阶段测试初始化失败，检查结果表为空。

### 与 PR 变更的关联
**与 PR 改动无关。** 该 PR 新增了 `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`（PostgreSQL 17.6 从源码编译）和配套 `entrypoint.sh`，Docker 镜像构建和推送阶段均成功完成：
- `[Build] finished`
- `[Push] finished`
- 镜像已成功推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`

失败发生在构建之后的 [Check] 阶段，即 `eulerpublisher` 工具使用 `shunit2` 对已构建的镜像运行功能验证测试时，因 CI 节点缺少 `shunit2` 而直接崩溃。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 节点上安装 `shunit2`，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中 `source shunit2` 能找到该框架。常见安装方式：
- `dnf install shunit2` 或 `yum install shunit2`
- 或将 `shunit2` 脚本放入 `eulerpublisher` 测试框架的依赖目录中

此问题为 CI 基础设施问题，**Code Fixer 无需对 PR 代码做任何修改**。

## 需要进一步确认的点
- 确认 `shunit2` 是否是 `eulerpublisher` 包的运行时依赖，若是，需在 `eulerpublisher` 的 RPM spec 中补充 `Requires: shunit2`，避免 CI 节点因缺少依赖而无法运行测试。
- 确认本次 CI 执行所在的节点是否与其他成功 PR 的构建节点一致——如果是临时更换的节点或新创建的节点，可能存在环境预置不完整的情况。

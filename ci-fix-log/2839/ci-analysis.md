# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, eulerpublisher, test failed

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
```

### 根因定位
- 失败位置: CI 运行器环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 检查阶段需要的 Shell 单元测试框架 `shunit2` 在运行器上未安装或不可用，导致整个 `[Check]` 阶段因测试框架加载失败而终止。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile（PostgreSQL 17.6 源码编译）和 entrypoint.sh 均构建成功：
- Docker 构建阶段全部完成（`#8 DONE 268.4s`）
- 镜像推送成功（`[Push] finished`）
- 镜像导出和 attestation 均正常（`#11 DONE 58.0s`）

失败仅发生在构建、推送完成后的 `[Check]` 阶段，`shunit2` 测试框架在 CI runner 上缺失导致无法执行镜像检查测试用例。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施修复**：在 CI runner 环境（负责镜像构建后检查的节点）上安装 `shunit2` Shell 单元测试框架。此问题需由 CI 管理员处理，Code Fixer 不需要对 PR 代码做任何修改。

## 需要进一步确认的点
- CI runner 节点上 `shunit2` 的安装路径是否符合 `common_funs.sh` 的 source 路径预期
- 同批次其他 PR 的 CI 检查阶段是否也出现同样的 `shunit2` 缺失错误（确认是否为偶发的基础设施问题）
- 检查 openEuler 24.03-LTS-SP4 的 CI runner 节点配置是否与已有的 22.03-LTS-SP4 / 24.03-LTS-SP2 节点一致

# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2` Shell 测试框架，导致 `eulerpublisher` 的 `[Check]` 阶段启动容器功能验证脚本时直接崩溃。构建表为空（无任何测试条目执行），确认测试框架未初始化即退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh，并更新了 README.md 和 meta.yml。日志显示 Docker 镜像构建（`#8 DONE 268.4s`）和推送（`[Push] finished`）均成功完成，PostgreSQL 源码编译、安装流程无任何异常。失败仅仅发生在 CI 工具链自身的 `[Check]` 容器验证阶段，该阶段的 shell 测试框架 `shunit2` 在 CI Runner 环境中不可用，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
向 CI 运维团队报告该 Runner 节点缺少 `shunit2` 依赖，请求在 CI Runner 环境（`/usr/local/etc/eulerpublisher/tests/` 目录层级）中安装或补充 `shunit2` 框架。此问题非 PR 代码层面可修，Code Fixer 无需对 Dockerfile 或任何 PR 文件做任何修改。

## 需要进一步确认的点
- 确认 CI Runner 上 `shunit2` 是否从未安装，还是本次构建使用了异常镜像版本的 Runner（如 Runner 镜像升级后丢失了 `shunit2`）。
- 确认同一仓库中其他镜像的 `[Check]` 阶段是否同样失败——如果是，属于全局性 Runner 环境退化；如果不是，需排查该 Runner 调度或构建环境的特异性。
- 若需要重试，建议触发 re-run 看是否在同一 Runner 上复现（排除单次环境波动）。

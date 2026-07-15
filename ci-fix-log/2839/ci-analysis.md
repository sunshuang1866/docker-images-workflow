# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, eulerpublisher, Check test failed

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
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试阶段（[Check]）依赖的 Shell 单元测试框架 `shunit2` 未安装在 CI runner 上，`common_funs.sh` 在第 13 行尝试 source/加载 `shunit2` 时失败，导致所有检查项均无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的变更仅为新增 openEuler 24.03-LTS-SP4 平台的 postgres 17.6 Dockerfile 及配套文件（entrypoint.sh、meta.yml、README.md）。日志显示 Docker 构建（`make && make install`）和镜像推送（`[Build] finished`、`[Push] finished`）均已成功完成，`#8 DONE 268.4s` 表明 PostgreSQL 源码编译安装完全通过。失败仅发生在 `eulerpublisher` 工具的 [Check] 阶段——该阶段需要 `shunit2` 测试框架来执行容器功能验证，而该框架在 CI runner 上缺失。

## 修复方向

### 方向 1（置信度: 高）
确认 CI runner 环境是否安装了 `shunit2`（Shell 单元测试框架）。若未安装，需在 CI runner 镜像或 provisioning 脚本中添加 `shunit2` 的安装步骤。该问题属于 CI 基础设施配置问题，与 PR 的 Dockerfile 代码无关，Code Fixer 无需对 PR 代码做任何修改。

### 方向 2（置信度: 低）
若 `shunit2` 是本应存在于 CI runner 上的工具但被意外移除，则联系 CI 运维团队检查 runner 环境变更历史，恢复 `shunit2` 的部署。

## 需要进一步确认的点
1. 确认 `shunit2` 在 CI runner 上的预期安装路径（`common_funs.sh:13` 期望从哪里加载它）。
2. 确认同一 CI runner 上其他成功通过 [Check] 阶段的 job（如同仓库其他 postgres 镜像构建）是如何加载 `shunit2` 的——即该问题是仅影响此 job 还是全局性的。
3. 确认 aarch64 架构构建 job 的日志是否存在独立的失败（当前日志仅包含 x86_64 构建，镜像 tag 为 `17.6-oe2403sp4-x86_64`）。

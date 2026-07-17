# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（同类——CI 工具依赖缺失）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架通用函数脚本，非 PR 代码）
- 失败原因: CI Runner 上缺少 `shunit2`（Shell 单元测试框架），`eulerpublisher` 的 [Check] 阶段无法运行容器测试。

### 与 PR 变更的关联
**无关**。PR 仅新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，并更新了 README.md 和 meta.yml。Docker 构建和镜像推送均已成功完成（`[Build] finished`、`[Push] finished`、镜像成功推送至 registry）。失败发生在 CI 工具链 `eulerpublisher` 的 [Check] 后测试阶段，与 PR 代码变更无任何关联。

日志中的两个 BuildKit 警告（`LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 26, 30)`）仅涉及 `ENV PGDATA /var/lib/pgsql/data` 和 `ENV PATH ${PATH}:/usr/local/pgsql/bin` 的写法风格，为非致命信息，不是失败原因。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 缺少 `shunit2` 工具。需要在 CI Runner 环境中安装 `shunit2`（可通过 `dnf install shunit2` 或 `git clone` 安装），或确保 CI 测试框架的依赖完整。此为纯基础设施问题，**Code Fixer 无需对 PR 代码做任何修改**。

## 需要进一步确认的点
- CI Runner 上是否应预装 `shunit2`，还是测试框架应自行提供？检查同类成功仓库（如其他 postgres 版本同仓库的其他 PR）的 CI Runner 配置。
- `shunit2` 是否在特定的 Runner 标签/节点上可用，而当前构建被调度到了一个未安装 `shunit2` 的节点？

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——无需修改代码）

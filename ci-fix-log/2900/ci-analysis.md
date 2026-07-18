# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（变体）
- 新模式标题: (不适用 — 匹配已知模式变体)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher` CI 框架的 `[Check]` 阶段 — 测试脚本 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI Runner 环境缺少 `shunit2`（Shell 单元测试框架），导致 `eulerpublisher` 的容器镜像校验阶段无法初始化测试，所有 Check Items 为空，整个 Check 阶段返回 CRITICAL 失败。Docker 镜像的构建（10/10 步骤全部 DONE）和推送（`[Push] finished`）均成功完成，失败仅发生在后置校验阶段。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`、`httpd-foreground` 辅助脚本，并更新了 `README.md`、`doc/image-info.yml`、`meta.yml` 等元数据文件。日志显示 Dockerfile 内所有 RUN 步骤均成功执行（从源码编译 httpd → `make install` → 配置修改 → 镜像导出推送），失败发生在 CI 框架层面的 `[Check]` 阶段，原因完全在于 CI Runner 缺少 `shunit2` 依赖。

此外，日志中出现一条非致命警告：
```
LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)
```
Dockerfile 第 5 行 `ENV HTTPD_PREFIX /usr/local/apache2` 使用了旧的 `ENV key value` 格式（正确写法应为 `ENV HTTPD_PREFIX=/usr/local/apache2`），但这仅为 BuildKit 风格建议，不影响构建结果。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 环境缺少 `shunit2` 包。需在 CI Runner 的测试环境镜像或配置中安装 `shunit2`（如在 openEuler 上通过 `dnf install shunit2` 安装，或确保 `common_funs.sh` 能找到 shunit2 的安装路径）。此问题与 PR 代码无关，属于 CI 基础设施维护范畴。

### 方向 2（置信度: 低 — 次要防患）
Dockerfile 第 5 行的 `ENV HTTPD_PREFIX /usr/local/apache2` 使用了旧式语法。虽非本次失败原因，但建议改为 `ENV HTTPD_PREFIX=/usr/local/apache2` 以消除 BuildKit 警告，保持代码库风格一致。

## 需要进一步确认的点
1. **shunit2 在 CI Runner 上的可用性**：确认当前 CI Runner（尤其是 24.03-lts-sp4 架构对应的 runner）是否安装了 `shunit2` 包，以及 `common_funs.sh` 引用 shunit2 的路径是否正确。
2. **是否为 SP4 专属问题**：检查同类 PR（如 SP2/SP3 版本的 httpd 或其他镜像）在近期 CI 运行中是否也出现 `shunit2: file not found` 错误，以判断是全局 CI 环境退化还是仅影响 SP4 runner。

## 修复验证要求
无需 code-fixer 操作。此问题为 CI 基础设施问题（infra-error），需由 CI 运维人员确认并修复 Runner 环境中的 `shunit2` 依赖。若确认 shunit2 已安装但路径不对，需更新 `common_funs.sh` 中的 shunit2 引用路径。Dockerfile 及 PR 代码变更本身无需修改。

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `CRITICAL: [Check] test failed`, `common_funs.sh`, `eulerpublisher`

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架脚本）
- 失败原因: CI Runner 的 eulerpublisher 测试框架依赖 `shunit2` 库，但该库未安装在 CI 运行环境中，导致 post-build 容器验证（[Check]）阶段脚本执行失败

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增的文件（`Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`、`httpd-foreground`、`meta.yml`、`README.md`、`doc/image-info.yml`）与 `shunit2` 测试框架无任何关联。证据如下：

- Docker 镜像**构建成功**：所有 7 个构建步骤均通过（`#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`）
- Docker 镜像**推送成功**：`[Build] finished` → `[Push] finished`，镜像已推送到 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`
- 失败仅发生在 eulerpublisher 的 `[Check]` 阶段，因 CI Runner 上缺少 `shunit2` 库导致测试脚本无法加载，检查结果表为空

Dockerfile 行 5 存在一个 BuildKit 警告（`LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format`），此为 ENV 格式风格建议，非致命错误，不影响构建结果。

## 修复方向

### 方向 1（置信度: 高）
CI 运维侧在 CI Runner 上安装 `shunit2` 测试框架（如在 openEuler 上通过 `dnf install shunit2` 或从源码安装到 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径下对应的可搜索位置）。此为 CI 基础设施问题，**Code Fixer 无需处理**。

## 需要进一步确认的点
- CI Runner 的 `shunit2` 安装状态：`common_funs.sh` 中通过 `. shunit2` 方式 source 该库，需确认：
  - `shunit2` 是否已在 Runner 上安装
  - 若已安装，其安装路径是否在 `common_funs.sh` 的 source 搜索路径中
  - 该问题是仅影响此 PR 还是所有 PR 的 [Check] 阶段均失败
- 构建日志中 Dockerfile 行 5 的 `LegacyKeyValueFormat` 警告为风格建议（建议 `ENV HTTPD_PREFIX=/usr/local/apache2`），不影响功能，但可在后续 PR 中修正

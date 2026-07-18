# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境的 [Check] 阶段测试框架 `shunit2` 未安装或不可用，`common_funs.sh` 脚本在尝试 source `shunit2` 时失败，导致整个测试脚本崩溃。测试结果表为空（0 项检查结果），说明测试框架在启动阶段就已退出，未能执行任何实际测试项。

### 与 PR 变更的关联
**无关**。PR 变更仅涉及新增 Dockerfile、httpd-foreground 启动脚本、更新 README/meta.yml/image-info.yml 文档。Docker 镜像构建（`#10 DONE 41.6s`，共 7 个步骤全部成功）和推送（`[Push] finished`）均已完成，只在后续 CI 工具链的 `[Check]` 容器验证阶段因 runner 缺少 `shunit2` 而失败。此外，日志中出现的 `LegacyKeyValueFormat` Docker 警告（第 5 行 `ENV HTTPD_PREFIX /usr/local/apache2` 格式风格）仅为非致命提示，不影响构建结果。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。该 runner 执行 `eulerpublisher` 的 `[Check]` 阶段时，`common_funs.sh` 需要 source `shunit2` 来运行容器功能验证测试，但当前 runner 环境缺少该依赖。安装后重新触发 CI 即可通过。

## 需要进一步确认的点
1. 确认 `shunit2` 是否应在 CI runner 镜像预装清单中，还是需要由 eulerpublisher 工具链自行管理该依赖。
2. 如果 `shunit2` 安装后测试仍失败，需进一步检查新增文件（Dockerfile、httpd-foreground）是否缺少 Copyright + SPDX-License-Identifier 头（参考模式17），因为当前 CI 的 Check 阶段在能执行任何测试前就崩溃了，无法判断此项是否合规。

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试环境 shunit2 缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 加载 shunit2 单元测试框架，但 CI runner 环境中未安装该工具，导致 [Check] 阶段的测试根本无法启动，`Check Items` 表格为空。

### 与 PR 变更的关联
**与 PR 无关。** Docker 镜像构建与推送均已成功完成：
- 构建阶段：`#10 DONE 41.6s`（configure + make + make install 全部通过）
- 配置阶段：`#11 DONE 0.1s`（groupadd/useradd/sed 配置均成功）
- 推送阶段：`[Build] finished` → `[Push] finished`
- 失败仅发生在 `eulerpublisher` 工具的 [Check] 测试阶段，属于 CI runner 环境问题。日志中唯一的 warning（`LegacyKeyValueFormat`）为非致命风格提示，不导致构建失败。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。具体操作取决于 CI 节点管理方式——可通过 RPM 包（openEuler 仓库中包名通常为 `shunit2`）或源码部署到 runner 的 `/usr/local/etc/eulerpublisher/tests/` 路径下。此修复属于 CI 基础设施维护，与 PR 代码无关。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 仓库中的确切包名（可能为 `shunit2` 或 `epel-release` 后通过 EPEL 安装）。
- 确认 CI [Check] 阶段依赖的 `shunit2` 是否应作为 `eulerpublisher` 包的 `Requires` 依赖自动安装——若是，需修复 `eulerpublisher` 的 RPM spec 文件。

## 修复验证要求
Code Fixer 无需处理此问题（infra-error，与 PR 代码无关）。

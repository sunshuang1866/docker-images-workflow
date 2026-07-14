# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试脚本 `common_funs.sh` 试图通过 `source`（`.`）加载 `shunit2` shell 单元测试框架，但该框架未安装在 CI runner 上，导致测试启动即失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 构建阶段（`meson setup` → `meson compile` → `meson install`）全部成功完成，422 个编译目标均通过，镜像成功构建并推送至 Docker Hub（`openeulertest/bind9:9.21.23-oe2403sp4-aarch64`）。从日志可见：
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功
- 失败仅发生在后续的 `[Check]` 阶段，原因是 CI runner 环境缺少 `shunit2` 测试框架，与本次 PR 新增的 Dockerfile 及配置文件变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner 上安装 `shunit2` shell 测试框架。在 openEuler 上可通过以下方式安装：
- `yum install shunit2` 或 `dnf install shunit2`
- 如仓库中无此包，可手动将 `shunit2` 脚本部署到 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 或 CI 运行环境可访问的路径。

### 方向 2（置信度: 低）
若 `shunit2` 无法安装，可在 CI `common_funs.sh` 中通过条件判断跳过 shunit2 依赖（如 `[ -f shunit2 ] && .shunit2 || return 0`），但这仅为 workaround，不建议采用。

## 需要进一步确认的点
- 确认该 CI runner 上其他成功通过 Check 阶段的 PR 是否有 `shunit2` 可用，以判断是本 runner 特有问题还是环境变更导致。
- 确认 `eulerpublisher` 工具包是否应在依赖中声明 `shunit2`，以及 CI runner 的初始化脚本是否遗漏了该依赖的安装。

## 修复验证要求
无需特殊验证——本次修复仅涉及 CI 基础设施，不涉及 PR 代码变更。

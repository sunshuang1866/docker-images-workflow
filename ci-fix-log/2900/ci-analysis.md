# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check, test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`:13
- 失败原因: CI 测试框架 `eulerpublisher` 的 `common_funs.sh` 脚本尝试 source `shunit2`（Shell 单元测试框架），但该工具未安装在 CI runner 环境中，导致 `[Check]` 阶段直接失败，检查结果表为空（无任何测试结果）。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。Docker 镜像构建阶段全部成功（`[Build] finished`），镜像推送也成功（`[Push] finished`），所有 7 个 Dockerfile RUN 步骤均正常完成。失败仅发生在 CI 编排工具 `eulerpublisher` 的 `[Check]` 后处理阶段——该阶段调用 `common_funs.sh` 对已构建镜像进行健康检查，因 `shunit2` 缺失而崩溃。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包。`shunit2` 是开源 Shell 单元测试框架（`brew install shunit2` / `apt install shunit2` / `yum install shunit2`），CI 编排工具 `eulerpublisher` 的测试脚本依赖它执行容器健康检查。需确认 CI runner 镜像中是否遗漏了该依赖。

## 需要进一步确认的点
1. 同一 CI runner 上其他 openEuler 24.03-LTS-SP4 镜像（非 httpd）的 Check 阶段是否也因 `shunit2` 缺失而失败？若失败范围更大，说明是 CI runner 环境整体缺少 `shunit2`；若仅 httpd-SP4 失败，则需确认 SP4 runner 节点与 SP2 runner 节点的环境差异。
2. 检查 `eulerpublisher` 的容器测试框架是否在 24.03-LTS-SP4 runner 上安装 `shunit2` 作为前提依赖，该依赖是否遗漏在 SP4 runner 的初始化脚本中。

## 修复验证要求
无需 code-fixer 参与。该问题属于 CI 基础设施配置问题，应由 CI 管理员在 runner 节点上安装 `shunit2` 后重试。

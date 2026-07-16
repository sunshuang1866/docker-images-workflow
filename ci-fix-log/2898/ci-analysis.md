# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: 测试脚本 `common_funs.sh`:13（CI [Check] 阶段，非 Dockerfile）
- 失败原因: CI runner 上缺少 `shunit2` Shell 测试框架，`common_funs.sh` 第 13 行尝试 source 该工具时失败，导致镜像构建后的校验测试无法执行。

Docker 镜像构建和推送本身均已成功完成：
- `[Build] finished` — 镜像构建成功
- `[Push] finished` — 镜像推送成功
- 失败仅发生在构建后的 `[Check]` 测试阶段

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个 Go 1.25.6 on openEuler 24.03-LTS-SP4 的 Dockerfile 及配套的 README、image-info.yml、meta.yml 条目更新，属于标准的版本新增操作。`shunit2` 缺失是 CI 运行环境的基础设施问题，与本次代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI 构建节点的运行环境中安装 `shunit2`（shUnit2 Shell 单元测试框架）。该工具是 `common_funs.sh` 测试脚本的运行时依赖，缺失导致所有镜像的 `[Check]` 校验阶段均会失败。具体操作：在 CI runner 上通过包管理器安装 `shunit2`（如 `dnf install shunit2` 或 `yum install shunit2`）。

## 需要进一步确认的点
- 确认 CI runner 镜像模板是否近期变更，导致 `shunit2` 被移除（检查其他成功构建的同类型 PR 日志）
- 确认 openEuler 24.03-LTS-SP4 的软件源中是否包含 `shunit2` 包，或是否需要通过其他方式安装（如 pip、git clone 等）
- 检查是仅 `aarch64` 节点还是所有架构节点都存在 `shunit2` 缺失问题（本次日志仅展示 aarch64 构建）

## 修复验证要求
无需 Dockerfile 层面修改。Code Fixer 应提交一个仅包含 CI 环境修复（安装 `shunit2`）或 rerun CI 的请求。若 CI 环境不支持直接安装，可考虑在 `common_funs.sh` 中将 `shunit2` 的引用路径改为可下载的远程源或容器内预装。

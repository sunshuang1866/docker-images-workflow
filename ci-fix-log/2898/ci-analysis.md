# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI检查工具缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境中的测试脚本 `common_funs.sh` 第 13 行需要 `source` 引入 `shunit2`（一个 Shell 单元测试框架），但该工具在 CI runner 上未安装或不在 `PATH` 中。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），无任何代码层面的问题。Docker 镜像的构建阶段（#7～#11）和推送阶段均**完全成功**（`[Build] finished`、`[Push] finished`、`exporting manifest sha256:03184775... done`）。失败仅发生在 CI 流水线的 `[Check]` 测试验证阶段，原因是 CI runner 自身的测试工具链不完整（缺少 `shunit2`）。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的基础环境镜像或初始化脚本中安装 `shunit2`：
- 对于使用 `dnf` 的 openEuler 环境：`dnf install -y shunit2`（需确认该包在 openEuler 仓库中的包名，可能为 `shunit2` 或 `shUnit2`）
- 对于其他 Linux 发行版：通过包管理器安装，或从 GitHub 仓库 `kward/shunit2` 下载脚本放置到 `/usr/local/bin/` 或 CI 测试脚本可检索的路径中

### 方向 2（置信度: 低，补充说明）
如果本次构建的 aarch64 架构构建和检查均通过（日志显示 aarch64 构建成功），而 x86_64（amd64）构建日志未在本次输入中提供，那 x86_64 的构建可能也存在其他问题。但从现有的 aarch64 日志来看，构建本身无异常，`shunit2` 缺失是一个全局性 CI 基础设施问题，无论哪种架构都会触发。

## 需要进一步确认的点
1. 确认 CI runner 的操作系统版本和包管理器，以确定正确的 `shunit2` 安装方式（`dnf install shunit2` vs 从 GitHub 下载脚本）
2. 确认 x86_64（amd64）架构的构建日志，排除 x86_64 构建是否存在独立于 `shunit2` 缺失的其他失败原因
3. 确认该 CI runner 上 `shunit2` 是否原本就应预装（即是否 CI 环境初始化模板遗漏了该依赖），还是本次是首次在 Go 镜像中触发 `[Check]` 测试阶段导致该问题暴露

## 修复验证要求
此问题为 CI 基础设施问题（infra-error），修复无需修改任何 PR 中的文件。验证方法：在安装 `shunit2` 后重新触发 CI 构建，确认 `[Check]` 阶段通过即可。

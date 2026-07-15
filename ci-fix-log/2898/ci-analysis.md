# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 编排工具 `eulerpublisher` 的 `[Check]` 测试阶段
- 失败原因: CI runner 环境中缺少 `shunit2`（Shell 单元测试框架），导致 `common_funs.sh` 脚本第 13 行 `source shunit2` 失败，容器功能验证（Check）步骤无法执行。Docker 镜像的构建和推送均已成功完成（`[Build] finished`、`[Push] finished`、镜像成功推送至 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`）。

### 与 PR 变更的关联
与 PR 变更无关。PR 仅新增了一个 Go 1.25.6 on openEuler 24.03-LTS-SP4 的 Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml），Docker 镜像构建本身完全成功。失败发生在 CI 自身测试框架的 shell 单元测试依赖（`shunit2`）缺失上，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2`（Shell 单元测试框架）。该工具是 `eulerpublisher` 容器测试脚本 `common_funs.sh` 的运行时依赖，需确保所有负责 `[Check]` 阶段的 CI runner 节点已预装此工具。

## 需要进一步确认的点
- `shunit2` 是应通过包管理器安装（如 `dnf install shunit2`）还是手动部署到 `/usr/local/etc/eulerpublisher/tests/` 目录下
- 此问题是否仅影响新增的 SP4 架构 runner 节点（其他 SP3/SP2 runner 是否也缺少 `shunit2`）
- 是否存在其他受影响的待测镜像（非本 PR 范围）

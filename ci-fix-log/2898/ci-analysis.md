# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试工具缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试环境中的 `eulerpublisher` 容器检查脚本 `common_funs.sh` 依赖 `shunit2`（Shell 单元测试框架），但 `shunit2` 未被安装在 CI runner 上或不在 `PATH` 中，导致 `[Check]` 阶段直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增 Go 1.25.6 的 Dockerfile（`Others/go/1.25.6/24.03-lts-sp4/Dockerfile`）及相关元数据文件（`README.md`、`image-info.yml`、`meta.yml`），属于纯配置/文档级别变更。Docker 镜像的构建和推送均成功完成：

- `#7 DONE 67.8s` — Go 源码下载与解压成功
- `#8 DONE 40.5s` — 文件时间戳及符号链接创建成功
- `#9 DONE 1.5s` — 编译工具卸载与清理成功
- `#11 DONE 41.9s` — 镜像导出与推送成功
- `[Build] finished` + `[Push] finished` — eulerpublisher 确认构建与推送完成

失败发生在构建和推送全部成功之后的 `[Check]` 阶段，该阶段由 `eulerpublisher` 框架调用 `common_funs.sh` 对已构建的镜像执行运行时验证，因 `shunit2` 缺失而直接崩溃——这不是 PR 代码引入的问题。

## 修复方向

### 方向 1（置信度: 高）
CI 环境中缺少 `shunit2` 测试框架。需要在 CI runner（`ecs-build-docker-aarch64-01-sp` 等）上安装 `shunit2`，或在 `eulerpublisher` 的容器测试依赖中补充该工具。常见的安装方式：

- openEuler 仓库：`dnf install shunit2`（如果仓库中有该包）
- 手动下载：从 [GitHub - kward/shunit2](https://github.com/kward/shunit2) 获取并放入测试脚本的 `PATH` 中

此问题与本次 PR 的 Dockerfile 变更无关，应由 CI 基础设施维护者处理。

### 方向 2（置信度: 低）
若 `shunit2` 在 CI 环境中已安装但路径不在 `PATH` 中，需检查 `common_funs.sh` 中对 `shunit2` 的引用方式（如是否使用了硬编码路径），并修正为绝对路径或将 shunit2 目录加入 `PATH`。

## 需要进一步确认的点
- 检查 CI aarch64 runner（`ecs-build-docker-aarch64-01-sp`）上是否安装了 `shunit2`（执行 `which shunit2` 或 `dnf list installed | grep shunit2`）
- 检查 x86_64 架构的 CI runner 上同类 Go 镜像构建是否也会在此处失败（本次日志仅包含 aarch64 构建的完整日志）
- 确认 `eulerpublisher` 的 `common_funs.sh` 中是如何引用 `shunit2` 的（第 13 行的具体命令）

## 修复验证要求
无需验证。本故障为 CI 基础设施问题，与 PR 代码无关。PR 中的 Dockerfile 和元数据文件无需修改。CI 基础镜像维护者修复 `shunit2` 缺失问题后重新触发构建即可通过。

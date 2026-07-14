# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 检查阶段shunit2缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 基础设施文件 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI Runner 环境缺少 `shunit2`（Shell 单元测试框架），导致 eulerpublisher 的 [Check] 阶段在 source `common_funs.sh` 时因找不到 `shunit2` 文件而失败。Docker 镜像的构建（[Build] finished）和推送（[Push] finished）均已成功完成。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关配置文件（named.conf、meta.yml、image-info.yml、README.md）。从日志中可见，Docker 镜像构建阶段（`meson setup && meson compile && meson install`）全部通过，镜像成功推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。失败发生在 CI 工具 eulerpublisher 自身的 Check 阶段，根本原因是 runner 环境缺少 `shunit2` shell 测试框架，与该 PR 的任何代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2`。`shunit2` 是一个 Shell 脚本单元测试框架，可通过以下方式之一安装：
- 通过系统包管理器安装（如 `dnf install shunit2`）
- 从 [GitHub](https://github.com/kward/shunit2) 下载并置于 `PATH` 中的合适位置
- 在 CI Runner 的初始化脚本中添加 `shunit2` 的部署步骤

### 方向 2（置信度: 低）
若 Runner 环境的确已安装 `shunit2`，但未被 `common_funs.sh` 正确定位，则需要检查 `common_funs.sh` 第 13 行中 `shunit2` 的引用路径是否正确（是使用 `source` 相对路径还是依赖 `PATH`）。

## 需要进一步确认的点
- 同仓库其他最近成功构建的 PR（如其他 Docker 镜像的 PR）在 Check 阶段是否也遇到 `shunit2: file not found` 错误。若是，则为全局 CI Runner 环境问题；若否，则需确认本 PR 触发的构建是否被调度到了一个配置缺失的 Runner 节点。
- `shunit2` 是否已在 Runner 镜像/模板中预装，或需要作为 CI 前置步骤安装。

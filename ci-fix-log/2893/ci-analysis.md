# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 Shell 公共函数脚本在 line 13 尝试 source `shunit2`（Shell 单元测试框架），但该文件在 CI runner 上不存在，导致 `[Check]` 测试阶段直接失败。

### 与 PR 变更的关联
**与 PR 无关**。本次 PR 仅新增 bind9 的 Dockerfile（`Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`）、配置文件（`named.conf`）及文档更新（README.md、image-info.yml、meta.yml）。Docker 镜像的 Build 和 Push 阶段均已成功完成：

- `[Build] finished` — 422/422 编译目标全部通过，meson install 成功（日志 #9 全程无编译错误）
- `[Push] finished` — 镜像 `openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 已推送至 Docker Hub（sha256:7a2bec1b…）

失败发生在 CI 框架的 `[Check]` 阶段，是 `eulerpublisher` 测试框架自身依赖 `shunit2` 缺失导致的环境问题，与本次 PR 的代码变更完全无关。镜像本身构建正常，无需修改 Dockerfile。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` Shell 测试框架。需在 CI runner 的基础环境镜像或初始化脚本中预装 `shunit2`，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能正确 source 到该文件。

### 方向 2（置信度: 低）
若 `shunit2` 本应由 eulerpublisher 测试框架自带（如存放在框架的 vendor/lib 目录下），则可能是本次使用的 runner 上 eulerpublisher 安装不完整或路径配置错误，需检查 eulerpublisher 的部署完整性。

## 需要进一步确认的点
- `shunit2` 是 eulerpublisher 框架的自带依赖还是需要 CI runner 另行安装的系统依赖？
- 其他近期的 PR（如同样使用 SP4 基础镜像的镜像）在 `[Check]` 阶段是否也遇到相同错误？（确认是本次 runner 的个别问题还是新 runner 镜像的普遍问题）
- `common_funs.sh` 中 source `shunit2` 是否依赖 `SHUNIT2_HOME` 或 `PATH` 等环境变量，这些变量是否在 CI runner 上正确配置？

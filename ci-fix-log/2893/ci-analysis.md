# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 环境 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI Runner（aarch64 节点）上缺少 `shunit2` Shell 测试框架，eulerpublisher 的公共测试脚本 `common_funs.sh` 在 source `shunit2` 时未找到该文件，导致 [Check] 阶段直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 bind9 的 Dockerfile、named.conf，并更新 README.md、image-info.yml、meta.yml 四个文件。Docker 镜像构建（meson compile 422/422 目标全部完成）和推送均已成功，失败仅发生在 CI 后处理/检查阶段——`shunit2` 是 CI 运行环境的基础测试依赖，不受任何 Dockerfile 或 PR 文件控制。

## 修复方向

### 方向 1（置信度: 高）
CI 维护者在 aarch64 构建 Runner 上安装 `shunit2` Shell 测试框架。`shunit2` 可通过包管理器（如 `yum install shunit2`）或手动下载（https://github.com/kward/shunit2）部署到 Runner 的 `PATH` 或 `/usr/share/` 目录中。此修复与 PR 代码无关，无需修改任何 Dockerfile 或元数据文件。

## 需要进一步确认的点
1. 确认 `shunit2` 在 aarch64 Runner 上的预期安装路径及安装方式（yum 包？手动部署脚本？）
2. 排查是否仅 aarch64 Runner 缺少 `shunit2`，还是 x86_64 Runner 也存在同样问题（日志仅覆盖 aarch64 架构的构建和检查过程）

## 修复验证要求
无。本次失败为 infra-error，不涉及 PR 代码修改，无需 code-fixer 进行任何源码或配置变更。CI 基础设施修复后重新触发流水线即可验证。

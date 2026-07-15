# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架脚本）
- 失败原因: CI Runner 环境中缺少 `shunit2` shell 测试框架库。Docker 镜像构建与推送均已完成且成功（422/422 个编译目标全部通过，镜像导出并推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`），失败仅发生在构建完成后的 `[Check]` 测试阶段，即 `eulerpublisher` 的容器启动校验脚本尝试 `source shunit2` 时找不到该文件。

### 与 PR 变更的关联
本次 PR 变更仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 Dockerfile、named.conf、meta.yml、README.md、image-info.yml），所有新增文��内容与 `shunit2` 测试框架无关。Docker 镜像构建阶段已成功完成，证明 PR 代码变更本身无问题。失败根因是 CI 基础设施中 `shunit2` 未安装，与 PR 变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 镜像或构建节点上安装 `shunit2` shell 测试框架。`shunit2` 是一个开源的 xUnit 风格 shell 单元测试框架，通常通过系统包管理器（如 `yum install shunit2` 或 `apt install shunit2`）安装，也可从 GitHub（kward/shunit2）获取后放入 PATH。此修复属于 CI 基础设施运维操作，Code Fixer 无需处理 PR 仓库中的任何文件。

## 需要进一步确认的点
- 确认 CI Runner 环境中 `shunit2` 的预期安装路径（当前脚本从 `$PATH` 搜索或硬编码路径中 source）以及安装方式（RPM 包名 vs 手动部署）。
- 确认是否只有此 aarch64 runner 缺少 `shunit2`，还是所有构建节点均存在此问题。

# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 运行环境的 `[Check]` 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI Runner 环境中未安装 `shunit2` 测试框架，`common_funs.sh` 在第 13 行 `source`（`.` 命令）加载 `shunit2` 时文件不存在，导致容器启动校验（Check 阶段）失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、`named.conf` 配置文件，并更新了 README.md、doc/image-info.yml、meta.yml 等文档/元数据文件。Docker 镜像的构建（meson compile + install）、推送（push to docker.io）均已成功完成（422 个编译目标全部链接通过，镜像 manifest 推送完成），失败发生在构建完成后的容器启动校验阶段——该阶段依赖 `shunit2` 框架，是 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题：在运行 Check 测试的 CI Runner 环境中安装 `shunit2`。`shunit2` 是一个 Shell 单元测试框架，通常可通过包管理器安装（如 `yum install shunit2` 或 `pip install shunit2`），或手动将 `shunit2` 脚本部署到 `/usr/local/etc/eulerpublisher/tests/common/` 目录下。

## 需要进一步确认的点
1. 确认 `shunit2` 是否应作为 CI Runner 的基础环境预装组件，还是本次 PR 构建的 Runner 临时缺少该组件。
2. 确认同一 PR 其他架构（如 x86_64/amd64）的构建 job 是否也因相同原因失败——日志中仅包含 aarch64 的构建和检查记录。
3. 确认 `shunit2` 的预期安装路径和版本，是否与 `common_funs.sh` 中 `. shunit2` 的引用方式兼容（当前为不带路径的直接 source，依赖 `PATH` 或同目录存在）。

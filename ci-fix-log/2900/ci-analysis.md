# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架 shunit2 缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check, test failed, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 测试框架 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 上缺少 `shunit2`（Shell 单元测试框架），`common_funs.sh` 脚本尝试通过 `.` 命令 source `shunit2` 时找不到该文件，导致 [Check] 阶段直接失败

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2900 仅新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`、`httpd-foreground` 启动脚本，以及更新 README.md、image-info.yml 和 meta.yml 等文档元数据文件。Docker 镜像构建和推送阶段均已成功完成（日志中 `#14 DONE 31.3s`，`[Build] finished`，`[Push] finished`），失败发生在 CI 基础设施层的测试框架启动阶段，属于 CI 运行环境自身问题。

## 修复方向

### 方向 1（置信度: 高）
CI 运维团队需在 Runner 环境上安装 `shunit2` 测试框架。openEuler 环境下可通过包管理器安装：
- 确认 `shunit2` 包的可用性（在 openEuler 仓库中可能名为 `shunit2` 或 `shunit`）
- 在 CI Runner 初始化脚本中确保 `shunit2` 已事先安装于 `/usr/local/etc/eulerpublisher/tests/container/common/` 或系统可搜索路径中

### 方向 2（置信度: 中）
若 `shunit2` 在 openEuler 24.03-LTS-SP4 软件源中不可用，可从上游源码（[shunit2 GitHub](https://github.com/kward/shunit2)）手动部署到 CI Runner 环境，或由 `eulerpublisher` 测试框架自行内置 shunit2 而不依赖系统安装。

## 需要进一步确认的点
1. `shunit2` 在 openEuler 24.03-LTS-SP4 的 yum/dnf 源中是否可用（包名可能为 `shunit2` 或 `shunit`）
2. CI Runner 的初始化/置备流程中是否有安装 shunit2 的步骤被遗漏或失效
3. 该问题是否为该 CI Runner 的特定环境问题（例如是 x86_64 架构专属还是所有架构 Runner 均受影响）
4. 同类镜像的其他 PR（如之前已合入的 httpd 2.4.66-oe2403sp2）在 CI 的 [Check] 阶段是否也遇到相同的 shunit2 缺失问题

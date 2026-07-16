# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 缺 shunit2
- 新模式症状关键词: `shunit2: file not found`, `Check] test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 的 `[Check]` 阶段
- 失败原因: CI 测试框架 `shunit2`（Shell 单元测试库）未安装在 Runner 上。`common_funs.sh` 脚本第 13 行通过 `source`（`.`）引用了 `shunit2`，但该文件在 Runner 的搜索路径中不存在。Docker 镜像的构建（422/422 编译目标全部成功）和推送（`[Push] finished`）均已正常完成，失败仅发生在镜像构建后的容器校验测试阶段。

### 与 PR 变更的关联
与 PR 变更无关。PR 的改动仅为新增 `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile` 和配套配置文件（`named.conf`）、更新 README 和 meta.yml。Docker 构建和推送阶段均顺利完成，所有 422 个编译目标链接成功并安装完毕。失败是 CI 基础设施中 `shunit2` 未安装所致，与任何代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在对应架构的 CI Runner 上安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 单元测试库，可通过包管理器安装（如 `dnf install shunit2` 或从 GitHub 克隆安装），使 `[Check]` 阶段的容器校验测试能正常执行。

## 需要进一步确认的点
- 确认是否仅 aarch64 Runner 缺少 `shunit2`，还是 x86_64 Runner 也有同样问题
- 确认是否有多个 CI Runner 需要补充安装 `shunit2`
- 若上游镜像已推送成功（`openeulertest/bind9:9.21.23-oe2403sp4-aarch64`），可考虑绕过 Check 阶段重跑 CI 或手动确认镜像可用性

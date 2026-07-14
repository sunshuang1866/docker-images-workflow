# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: "shunit2测试框架缺失"
- 新模式症状关键词: "shunit2, file not found, .: shunit2, common_funs.sh, eulerpublisher"

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 流水线的 [Check] 阶段在运行容器功能测试时，`common_funs.sh` 试图通过 `.` 命令加载 `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在 CI runner 环境中，导致测试脚本执行失败。

**Docker 镜像构建和推送均完全成功**：
- `meson setup` + `meson compile` 全部 422/422 个编译目标通过（日志显示 `[422/422] Linking target named`）
- `meson install` 成功安装所有库文件到 `/usr/lib64`、所有二进制到 `/usr/bin` 和 `/usr/sbin`
- Docker 镜像导出和推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 均完成（`#13 DONE 36.0s`）
- `[Build] finished` 和 `[Push] finished` 日志均正常输出

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增一个 bind9 9.21.23 Dockerfile（构建成功）、named.conf 配置文件、更新 README.md/image-info.yml/meta.yml 的文档条目。失败发生在 CI 测试基础设施层（`eulerpublisher` 容器的 [Check] 测试阶段），`shunit2` 缺失是 CI runner 环境问题，非 Dockerfile 或任何 PR 代码导致。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2` Shell 测试框架。`shunit2` 通常可通过系统包管理器安装（`yum install shunit2` 或 `dnf install shunit2`），或从 GitHub 下载后置于 `PATH` 中以供 `eulerpublisher` 的测试脚本加载。这是 CI 基础设施维护工作，Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- 确认 CI runner 节点上 `shunit2` 包是否可用（`dnf search shunit2`），若 openEuler 仓库不提供，需将 `shunit2` 脚本预置到 runner 的 `PATH` 中。
- 确认本次 CI 是否仅提交了 aarch64 架构的构建（日志中镜像 tag 为 `…-aarch64`），x86_64 架构是否也有同样的 [Check] 阶段 `shunit2` 缺失问题。

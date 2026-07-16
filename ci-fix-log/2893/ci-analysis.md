# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
```

### 根因定位
- 失败位置: CI 测试编排器 `eulerpublisher` 的 `[Check]` 阶段，`common_funs.sh:13`
- 失败原因: CI runner 的测试环境中缺少 `shunit2`（Shell 单元测试框架），`common_funs.sh` 在第 13 行尝试 `. shunit2` 时找不到该文件，导致容器镜像的启动检查 (`[Check]`) 无法执行，整个 pipeline 被标记为 FAILURE。

### 与 PR 变更的关联
**与 PR 代码变更无关。** Docker 镜像的构建和推送阶段均成功完成：
- 所有 422 个 meson 编译目标成功编译和链接
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功（镜像 sha256:7a2bec1b... 已推送到 docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64）

失败仅发生在 CI 自身的测试基础设施（`eulerpublisher` 的 `[Check]` 阶段）中，原因是在该 CI runner 上 `shunit2` 测试框架未安装或不在 `PATH` 中。PR 新增的 Dockerfile 中已正确安装 `shadow-utils`（包含 `groupadd`/`useradd`），所有后续 `RUN` 命令均执行成功。

## 修复方向

### 方向 1（置信度: 低）
这是一个 CI 基础设施问题，需要在 CI runner 镜像中安装 `shunit2` 框架（如通过 `dnf install shunit2` 或手动将 `shunit2` 脚本放入 `PATH`）。**PR 作者无需修改 Dockerfile 或任何代码**。建议联系 CI 运维团队检查该 runner 的测试环境配置。

## 需要进一步确认的点
1. 该 CI runner（构建 aarch64 镜像的节点）的测试环境中是否安装了 `shunit2` 包？可通过 `which shunit2` 或 `rpm -q shunit2` 验证。
2. 其他同类型的 PR（如其他镜像在 openEuler 24.03-LTS-SP4 上的新增 Dockerfile）是否也遇到相同的 `[Check] test failed` 问题？如果普遍存在，可确认为 CI 基础设施问题。
3. `eulerpublisher` 工具中的 `common_funs.sh` 预期 `shunit2` 的安装路径是什么？需要确认安装约定。

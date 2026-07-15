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
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `eulerpublisher` 容器检查阶段（`app.py:173`），具体触发点在 `common_funs.sh:13`
- 失败原因: CI 测试环境的 `common_funs.sh` 脚本尝试 `source shunit2`（shUnit2 测试框架），但 `shunit2` 未安装或不在 `$PATH` 中，导致 `[Check]` 阶段立即失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2893 仅新增了 `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile` 及配套的 `named.conf`、`meta.yml`、`image-info.yml` 和 README 条目，且 Docker 镜像构建阶段完全成功：
- 编译阶段：全部 422 个编译目标通过
- 链接阶段：所有二进制和库链接成功
- meson install：所有文件安装到目标路径
- Docker 构建：步骤 #10~#12 全部 `DONE`
- 推送阶段：`[Push] finished`，镜像 `openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 成功推送至 registry

失败仅发生在 CI 编排工具 `eulerpublisher` 的后置 `[Check]` 阶段，该阶段依赖 `shunit2` 测试框架做容器健康检查，因其缺失而崩溃。这是 CI runner 环境配置问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI 构建节点的 `eulerpublisher` 运行环境中安装 `shunit2`（shUnit2 shell 单元测试框架）。可从发行版包管理器安装（如 `dnf install shunit2`）或从 upstream 下载后放入 `common_funs.sh` 可寻找到的路径。

## 需要进一步确认的点
- 确认 CI runner 环境原本是否就已安装 `shunit2`，以及本次是否因环境变更导致丢失。
- 确认 `common_funs.sh` 中 `shunit2` 的预期安装路径（`line 13` 附近的 `. shunit2` 实际是 `source /path/to/shunit2` 还是直接 `source shunit2`），以确定需要将 shunit2 部署到哪个目录或 PATH 中。

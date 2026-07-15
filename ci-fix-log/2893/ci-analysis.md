# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试环境中 `shunit2`（Shell 单元测试框架）文件缺失，`common_funs.sh` 脚本第 13 行尝试 `source` 该框架时找不到文件，导致镜像构建后的 [Check] 健康检查阶段失败。Docker 构建（#9 编译 422 目标全部通过）和推送（#13 push 成功）均已完成，失败仅发生在测试后处理阶段。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bind9 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置及元数据更新（README.md、image-info.yml、meta.yml）。日志中 Docker 镜像构建（`meson setup/compile/install` 422 个目标全部通过）和推送流程均成功完成，失败发生在 CI 后处理阶段，原因是 CI runner 上的 `eulerpublisher` 测试框架缺少 `shunit2` 依赖文件。这是 CI 基础设施问题，非代码问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 镜像或测试环境中安装 `shunit2` 框架。`common_funs.sh` 第 13 行需要 `shunit2` 文件可被 `source`，应确保该文件位于脚本能搜索到的路径（如 `PATH`、与脚本同目录、或绝对路径指向）。这是 CI 运维层面的修复，无需修改 PR 中的任何文件。

## 需要进一步确认的点
- CI runner 上 `shunit2` 原本是否应存在于 `/usr/local/etc/eulerpublisher/tests/container/common/` 或类似路径下
- 该 runner 是否为 aarch64 架构（镜像 tag 为 `9.21.23-oe2403sp4-aarch64`），是否存在架构专属的测试环境依赖差异
- 其他同类镜像的 CI 构建是否也出现相同问题（可用于确认是单次 runner 环境异常还是环境配置变更导致）

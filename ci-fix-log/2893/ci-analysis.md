# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI runner 上 eulerpublisher 测试框架 `common_funs.sh:13`
- 失败原因: eulerpublisher 的 [Check] 步骤在初始化测试框架时，无法找到 `shunit2` 依赖（shell 单元测试库），导致检查步骤在约 10ms 内立即失败。Docker 镜像构建（422/422 编译目标均通过、`meson compile` 和 `meson install` 成功）、导出和推送均已成功完成。

### 与 PR 变更的关联
与 PR 变更无关。该 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件，以及 README.md / image-info.yml / meta.yml 的元数据更新。Docker 构建全流程成功，失败仅发生在 CI 工具 eulerpublisher 的 [Check] 后处理阶段，属于 CI 基础设施依赖缺失问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。`shunit2` 是 eulerpublisher 的 Check 流程所依赖的 shell 单元测试库，缺它会导致所有镜像的 [Check] 步骤失败。确认 `shunit2` 应作为 eulerpublisher 的运行时依赖打包，或作为系统包安装在 CI runner 镜像中（需确认安装路径为 `/usr/local/etc/eulerpublisher/tests/container/common/` 或系统 PATH 可及位置）。

## 需要进一步确认的点
- `shunit2` 是否应作为 `eulerpublisher` Python 包的一部分分发（随 `pip install` 一起安装到 `/usr/local/etc/eulerpublisher/tests/` 下），还是作为独立的系统级依赖通过 `yum`/`apt` 安装
- 同 PR 中 SP3 版本的 Check 是否也遇到相同问题（日志中仅包含 SP4 aarch64 的构建，需确认其他已存在的 bind9 版本在相同 CI runner 上的 Check 是否也失败，以排除 runner 环境全局性问题）
- 日志中的构建仅覆盖 aarch64 架构；x86_64 架构的构建结果未知，但预期与 aarch64 保持一致（构建成功、Check 因相同原因失败）

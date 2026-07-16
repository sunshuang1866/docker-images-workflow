# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `source`, `eulerpublisher`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 环境的 `eulerpublisher` 工具在执行 `[Check]` 阶段（容器镜像后置验证）时，其测试辅助脚本 `common_funs.sh` 第 13 行尝试通过 `. shunit2` 引入 `shunit2` 测试框架，但该框架文件在 CI runner 上不存在。

### 与 PR 变更的关联
本次 PR 的 Dockerfile、named.conf、meta.yml、README.md、image-info.yml 变更**与失败无关**：

1. **Docker 构建完全成功**：`meson setup` / `meson compile` / `meson install` 三个阶段均顺利完成，422 个编译单元全部编译通过并链接，所有二进制文件和手册页均安装到位。
2. **镜像推送成功**：`docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 已成功导出并推送至 registry。
3. **失败发生在 CI 后置检查阶段**：`[Check] test failed` 是由 `eulerpublisher` 容器测试框架的运行时依赖缺失（`shunit2` 未安装）导致，与 bind9 Dockerfile 内容、named.conf 配置、meta.yml 元数据均无任何关联。

日志中 `[Build] finished` 和 `[Push] finished` 均为 INFO 级别成功信息，唯一 CRITICAL 来自 `[Check]` 阶段的 `shunit2: file not found`。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境（或 `eulerpublisher` 容器镜像）中安装 `shunit2` shell 测试框架。`shunit2` 是一个标准的 xUnit 风格的 Shell 脚本测试库，通常通过包管理器安装（如 `dnf install shunit2` 或 `apt install shunit2`）或从源码部署到 `eulerpublisher` 的 `common/` 目录下。这不是 Dockerfile 或 PR 代码层面的修复，而是 CI 基础设施配置问题。

## 需要进一步确认的点
- 确认 `eulerpublisher` 工具对 `shunit2` 的依赖方式：是从系统 `PATH` 引入（需要 `shunit2` RPM/DEB 包安装），还是需要将 `shunit2` 脚本文件部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下。
- 确认同一 CI 环境下其他 PR 是否也因同一 `shunit2` 缺失而失败——若其他 PR 也失败，则为系统性问题，需运维修复 CI runner 镜像；若仅此 PR 失败，需排查是否 runner 配置异常。

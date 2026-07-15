# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）变体
- 新模式标题: (不适用，有历史模式参考)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架脚本）
- 失败原因: CI Runner 环境中缺少 `shunit2`（Shell 单元测试框架），导致 `eulerpublisher` 在 [Check] 阶段（容器镜像验证测试）无法加载测试库，测试步骤直接失败。Docker 镜像的构建（meson compile + install，全部 422 步）和推送均已成功完成。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`、`named.conf` 配置文件，以及更新了 `README.md`、`image-info.yml`、`meta.yml` 三条元数据。Docker 镜像构建阶段（包括 bind9 源码下载、meson 编译、二进制安装、用户/目录创建）全部通过，日志中可见所有 6 个 Dockerfile RUN 步骤均标注 `DONE`，push 也标注 `[Push] finished`。失败仅发生在 CI Pipeline 的容器验证阶段，原因是 CI Runner 的 `eulerpublisher` 测试环境缺少 `shunit2` 依赖。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施修复：在 CI Runner 环境（`ecs-build-docker-aarch64-01-sp` 或同类 aarch64 节点）中安装 `shunit2` 测试框架。该依赖应由 CI 运维团队在 Runner 镜像/初始化脚本中统一安装，**PR 作者无需修改 Dockerfile 或任何仓库代码**。可参考 openeuler 仓库中的安装方式（如 `dnf install shunit2 -y` 或从源码安装到 `/usr/local/etc/eulerpublisher/tests/` 路径下）。

### 方向 2（可选）
该 CI Runner 节点可能刚从基础镜像初始化，缺少完整的 `eulerpublisher` 测试套件依赖。可检查同批次其他 bind9 PR（如 24.03-lts-sp3 构建）是否也出现相同问题，以确认是单点 Runner 问题还是规模化依赖缺失。

## 需要进一步确认的点
1. `shunit2` 是否为 `eulerpublisher` 容器测试的强制依赖，还是仅在部分 runner 镜像中可选安装
2. 同批次其他 PR 的 aarch64 构建是否也因 `shunit2` 缺失而失败（判断是单节点问题还是全局 Runner 镜像回退）
3. 若 shunit2 已在 Runner 标准镜像中，需排查该 Runner 节点是否使用了非标准镜像或初始化流程异常

## 修复验证要求
（不适用 — 本失败为 `infra-error`，无需修改 PR 代码）

# CI 失败分析报告

## 基本信息
- PR: #2894 — chore(bisheng-jdk): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI工具依赖缺失
- 新模式症状关键词: ModuleNotFoundError, eulerpublisher, distroless

## 根因分析

### 直接错误
```
2026-07-09 20:31:20,936 - INFO - [Build] finished
2026-07-09 20:31:20,936 - INFO - [Push] finished
2026-07-09 20:31:20,936 - DEBUG - Shutting down executor...
Traceback (most recent call last):
  File "/usr/local/bin/eulerpublisher", line 6, in <module>
  File "/usr/local/lib/python3.9/site-packages/eulerpublisher/eulerpublisher.py", line 4, in <module>
  File "/usr/local/lib/python3.9/site-packages/eulerpublisher/container/cli.py", line 5, in <module>
ModuleNotFoundError: No module named 'eulerpublisher.container.distroless'
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/lib/python3.9/site-packages/eulerpublisher/container/cli.py:5`
- 失败原因: CI 编排工具 `eulerpublisher` 在 executor 关闭阶段启动时因缺少 `eulerpublisher.container.distroless` 模块而崩溃。Docker 镜像构建和推送本身均已成功完成（`#10 DONE 38.8s`，`[Build] finished`，`[Push] finished`），失败仅发生在 `eulerpublisher` 工具的后处理/清理阶段。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 `Others/bisheng-jdk/21.0.5/24.03-lts-sp4/Dockerfile` 及配套元数据文件（`meta.yml`、`image-info.yml`、`README.md`），均为标准 Dockerfile 和文档改动。Docker 构建阶段全部通过（JDK 下载、解压、smoke test 均成功），镜像已成功推送到 `docker.io/openeulertest/bisheng-jdk:21.0.5-oe2403sp4-aarch64`。`ModuleNotFoundError` 是 `eulerpublisher` Python 包自身的依赖问题，与 PR 代码变更无关。

### 附注：README/image-info.yml 文档描述不一致
PR 在 `README.md` 和 `image-info.yml` 中将该镜像描述为 "BiSheng JDK 21.0.5 on openEuler 22.03-LTS-SP4"，但实际基础镜像为 `openeuler/openeuler:24.03-lts-sp4`（即 24.03-LTS-SP4）。此处 `22.03` 应为 `24.03`，是文档笔误，不导致 CI 构建失败，但应在修复时一并更正。

## 修复方向

### 方向 1（置信度: 中）
CI 运维需检查 `eulerpublisher` Python 包在对应 Jenkins runner 上的安装完整性。具体而言，`eulerpublisher.container.distroless` 模块可能未被安装或随包版本升级后路径变更。修复手段为在 runner 上重新安装/更新 `eulerpublisher` 包，确保 `distroless` 子模块存在。**此问题不是 Code Fixer 可处理的范围，需 CI 运维团队介入。**

### 方向 2（置信度: 低）
如果 `distroless` 模块是新版本 `eulerpublisher` 新增的依赖但尚未在所有 runner 上部署，可能需要回退 `eulerpublisher` 版本或确保新旧版本的兼容性处理。

## 需要进一步确认的点
1. `eulerpublisher` 包的版本及其 `distroless` 子模块的安装状态——在本次构建的 aarch64 runner（以及对应的 amd64 runner）上是否一致。
2. 是否其他 PR 的 CI 构建也出现了相同的 `ModuleNotFoundError`——若为普适性问题，则确认是 CI 基础设施问题而非 PR 特有。
3. `eulerpublisher` 源码仓库中 `eulerpublisher/container/cli.py` 是否确实引用了 `distroless` 模块，以及该模块是否存在于源码中但在构建 wheel/包时被遗漏。
4. 本次构建为 aarch64（tag 中包含 `aarch64`），am64 架构的构建 job 日志未提供，无法确认两架构是否均触发此问题。

## 修复验证要求
无。本失败为 infra-error，与 PR 代码变更无关。Code Fixer 无需对 Dockerfile 或元数据文件做任何修改（但建议顺带修正 README.md 和 image-info.yml 中 `22.03` → `24.03` 的笔误）。

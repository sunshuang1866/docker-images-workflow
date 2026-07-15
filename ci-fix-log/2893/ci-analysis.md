# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check, test failed

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
- 失败位置: `eulerpublisher` CI 框架的 `[Check]` 测试阶段（位于 `app.py:173`）
- 失败原因: CI 环境的测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 加载 `shunit2` 测试框架，但该框架未安装在 CI runner 上，导致 `file not found`。Docker 镜像的构建（`[Build]`）和推送（`[Push]`）两个阶段均已成功完成。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套配置文件（`named.conf`、`meta.yml`、`README.md`、`image-info.yml`）。从日志可见，Docker 镜像的编译（422 个 C 编译单元全部通过）、安装和推送均成功完成：

- `#9 DONE 41.4s` — 编译与安装成功
- `[Build] finished` — 构建完成
- `[Push] finished` — 推送完成（`9.21.23-oe2403sp4-aarch64`）

失败仅发生在 `[Check]` 阶段，该阶段由 `eulerpublisher` 编排工具执行容器启动测试，但由于 CI 环境中缺少 `shunit2` 而无法运行测试脚本，与 PR 引入的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修复 PR 代码。** 这是 CI 基础设施问题：运行 build 的 aarch64 runner 上未安装 `shunit2` shell 测试框架。需要在 CI runner 镜像中安装 `shunit2` 包（如 `yum install shunit2` 或从 GitHub 获取），或调整 `eulerpublisher` 的测试编排逻辑使其在 `shunit2` 缺失时优雅降级而非报 CRITICAL。

### 方向 2（可选，置信度: 低）
查看 `aarch64` 以外的其他架构（如 `x86-64`）的构建 job 日志，确认是否同样因为 `shunit2` 缺失而失败，还是存在其他架构特定的问题。

## 需要进一步确认的点
1. CI runner 环境中是否有 `shunit2` 包可用（`yum search shunit2`），或需从 `https://github.com/kward/shunit2` 自行安装。
2. `eulerpublisher` 的 `common_funs.sh` 中 `shunit2` 的 source 路径是否正确，是否应改为绝对路径或预先安装的路径。
3. 同类仓库中其他 PR 是否在相同 CI 环境中也遇到 `shunit2: file not found` 问题（若是，则为 CI runner 镜像的系统性问题，非本次 PR 独有）。

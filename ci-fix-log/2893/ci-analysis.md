# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 [Check] 阶段时，尝试加载 shell 测试库 `shunit2`，但该文件在 CI runner 上不存在（`file not found`），导致容器检查脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 只新增了一个 bind9 的 Dockerfile（含 named.conf）并更新了 meta.yml、README.md 和 image-info.yml。Docker 镜像的编译、链接、安装和推送均完全成功：
- 全部 422 个编译目标通过（[422/422] Linking target named）
- meson 安装阶段无错误（Installing named to /usr/sbin 等）
- 镜像构建完成（#13 exporting to image ... done）
- 镜像推送完成（[Push] finished）

失败发生在 CI 自身的 [Check] 测试阶段，因 runner 上缺少 `shunit2` 测试库，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是标准 shell 单元测试库，可通过包管理器安装（如 `dnf install shunit2`）或手动部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径下。

### 方向 2（置信度: 低）
如果 `shunit2` 本应随 `eulerpublisher` 包自带（如放置在 `tests/container/common/` 目录下），则可能是 `eulerpublisher` 包版本更新导致该文件丢失，需修复 `eulerpublisher` 包的打包逻辑。

## 需要进一步确认的点
- 确认 CI runner 上 `shunit2` 的预期安装路径（`/usr/local/etc/eulerpublisher/tests/container/common/` 或系统路径）
- 确认 `shunit2` 在 openEuler 仓库中的包名（可能为 `shunit2`、`shunit` 或其他）
- 确认其他同类 PR 是否也遇到相同问题（如其他 openEuler 24.03-LTS-SP4 的新镜像 PR），以判断是偶发还是 CI 环境系统性问题

## 修复验证要求
无需额外验证。本失败为 infra-error，不涉及 PR 代码修改。

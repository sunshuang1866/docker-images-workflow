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
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 工具链 eulerpublisher 的 Check 阶段脚本）
- 失败原因: CI 测试框架 eulerpublisher 在 [Check] 阶段尝试通过 `common_funs.sh` 的 `line 13` 执行 `. shunit2` 以加载 shunit2 shell 测试库，但该库未安装在 CI runner 环境中，导致 Check 阶段脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR #2893 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、配置文件（named.conf）及对应的元数据条目（meta.yml、image-info.yml、README.md）。从日志可以清晰看到：

1. Docker 镜像构建完全成功 — `meson compile` 完成全部 422 个编译目标，`meson install` 正常安装，Docker 镜像导出和推送到 registry 均成功（`[Build] finished`、`[Push] finished`）。
2. 失败仅发生在后续的 eulerpublisher `[Check]` 阶段，该阶段依赖 `shunit2` 测试库进行容器启动检查，而 `shunit2` 在当前 CI runner 环境中不存在。

这是一个 CI 基础设施层面的问题，与本次 PR 的代码变更无因果关系。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架。openEuler 上可通过 `dnf install shunit2` 或从源码安装 shunit2 到 runner 的 PATH/库路径中，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中的 `. shunit2` 语句能正确找到该库。

### 方向 2（置信度: 低）
如果 shunit2 无法安装到全局，可修改 eulerpublisher 中的 `common_funs.sh`，将 `shunit2` 的来源路径改为一个相对于 eulerpublisher 安装目录的本地副本（如将 shunit2 脚本打包到 eulerpublisher 内部）。

## 需要进一步确认的点
1. 确认 CI runner 镜像中是否本应包含 `shunit2` 但当前版本的 runner 镜像缺失该包。
2. 确认其他 CI job（如 x86-64 架构的同版本构建）是否也遇到相同的 Check 阶段失败，以判断是全局性问题还是仅影响特定架构的 runner。
3. 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 仓库中的确切包名（可能为 `shunit2` 或 `shunit2` 相关名称）及可用的安装源。

## 修复验证要求
无需验证——此失败为 CI 基础设施问题，不涉及对 PR 中 Dockerfile 或任何源文件的修改。

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）— 同类但不完全相同（缺失的依赖不同）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896-INFO: [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 运行时环境中的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 `common_funs.sh` 脚本在第 13 行尝试通过 `. shunit2` 加载 `shunit2` shell 单元测试库，但该库文件在 CI runner 的文件系统中不存在，导致 Check 阶段（容器功能验证）完全无法启动。

### 与 PR 变更的关联
**与 PR 变更无关。** 

PR 变更内容为新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（`httpd-foreground` 启动脚本、`meta.yml`、`README.md`、`image-info.yml`）。CI 日志显示：

1. **Docker 构建成功**：`#10 DONE 41.6s`（configure → make → make install 全部完成）
2. **Docker 推送成功**：`#14 DONE 31.3s`（manifest 推送完成），日志明确输出 `[Build] finished` 和 `[Push] finished`
3. **失败发生在构建和推送之后**：Check 阶段因 CI 测试框架本身缺少 `shunit2` 依赖而无法执行任何容器测试，Check Results 表格完全为空

该失败属于 CI 基础设施层面的问题，与本次 PR 的 Dockerfile 代码无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` (`Shell Unit Testing Framework`)，使其对 `eulerpublisher` 的测试脚本 `common_funs.sh` 可用。具体需确认 `shunit2` 是否应被 `eulerpublisher` 打包为自身依赖，还是需要由 CI 编排系统预先部署到 runner 上（例如通过 `dnf install shunit2` 或 pip 安装 `shunit2`）。

### 方向 2（置信度: 低）
如果 `shunit2` 曾存在但被意外移除，检查 CI runner 镜像/环境的最新变更日志，确认 `shunit2` 是否因环境升级或清理操作被误删。

## 需要进一步确认的点
1. `shunit2` 是否应当由 `eulerpublisher` Python 包声明为依赖并在安装时自动部署？还是由 CI runner 的基础环境预装？
2. 该 CI runner（x86_64）上构建其他镜像时，Check 阶段是否也会遇到相同的 `shunit2: file not found` 错误？（若其他镜像的 Check 也失败，说明是 runner 环境整体缺少 shunit2；若仅此 PR 失败，需排查是否与 SP4 新镜像的检查配置有关）
3. Check Results 表格为空，是否意味着连"跳过检查"的默认流程都没有走到，`shunit2` 缺失直接导致了脚本的非零退出码？

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 上 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段（即 eulerpublisher 测试框架运行镜像功能测试时），测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 引入 shunit2 单元测试框架，但 CI Runner 环境中未安装该工具，导致 source 失败，[Check] 阶段中止。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`、`httpd-foreground` 启动脚本，以及 README、image-info.yml、meta.yml 的条目补充。镜像构建（Build）和推送（Push）阶段均已成功完成：

```
2026-07-10 09:18:18,406 - INFO - [Build] finished
2026-07-10 09:18:18,406 - INFO - [Push] finished
```

失败发生在构建成功之后的 [Check] 阶段，该阶段调用的是 CI 框架内建的测试基础设施（`eulerpublisher/tests/container`），`shunit2: file not found` 是 CI Runner 环境层面的缺失，与本次 PR 提交的 Dockerfile 或任何应用代码无关。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施维护**：在 CI Runner 节点上安装 `shunit2` 测试框架，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中的 `. shunit2` 能够找到该文件。

### 方向 2（置信度: 低）
如果 `shunit2` 应该是随 `eulerpublisher` 包一同部署到 CI 环境的（例如部署在特定搜索路径而非系统路径），则需检查 CI 环境中 `eulerpublisher` 包的部署完整性，确认 `shunit2` 文件是否被正确包含在发布包中。

## 需要进一步确认的点
- `shunit2` 在 CI Runner 环境中的预期安装路径是什么？是否需要由 eulerpublisher 包自带还是以系统包形式安装？
- 该 CI Runner 上其他同期运行的镜像 [Check] 测试是否也遇到同样的 `shunit2: file not found` 错误？可据此判断是单节点问题还是整体环境问题。
- 日志仅显示 `x86_64` 架构的构建，aarch64 架构的构建 job 日志未提供，若 aarch64 也失败需单独排查。

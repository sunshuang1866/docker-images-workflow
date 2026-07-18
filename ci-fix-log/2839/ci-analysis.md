# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 宿主环境的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 执行环境中缺少 `shunit2` 测试框架（shell 单元测试工具），`common_funs.sh` 脚本第 13 行尝试加载 `shunit2` 时失败，导致 [Check] 阶段的容器功能验证测试无法运行。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 证据如下：

1. Docker 镜像构建阶段完全成功：`#8 DONE 268.4s`，PostgreSQL 17.6 从源码编译到 `make install` 全部通过，`[Build] finished` 和 `[Push] finished` 均正常输出。
2. PR 变更仅包含 Dockerfile、entrypoint.sh、README.md 和 meta.yml 的新增/修改，不涉及 CI 基础设施配置。
3. 失败发生在 eulerpublisher 框架的 [Check] 阶段，该阶段使用 `shunit2` 对已构建完成的容器镜像进行运行时功能验证（如启动、连接测试），而非代码编译阶段。
4. `shunit2` 缺失是 CI Runner 环境问题，任何需要 [Check] 阶段验证的镜像构建都会触发相同错误。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 shell 脚本单元测试库，可通过以下方式安装（任选其一）：
- 通过包管理器安装（如在 openEuler 上 `dnf install shunit2` 或 `pip install shunit2`）
- 从 upstream 仓库手动部署到 CI Runner 的 `PATH` 中

### 方向 2（置信度: 低）
如果 `shunit2` 是 eulerpublisher 测试框架的内置依赖，则需排查 eulerpublisher 的安装流程是否完整，确认 `shunit2` 是否应从 eulerpublisher 的分发包中自带。

## 需要进一步确认的点
- `shunit2` 是 CI Runner 镜像的预装依赖还是 eulerpublisher 的运行时依赖？需确认 CI Runner 镜像的构建配置以及 eulerpublisher 的安装/部署流程。
- 同一 CI Runner 上其他同类镜像（如 postgres 的其他版本或其他 Database 镜像）的 [Check] 阶段是否同样失败？如果也在相同阶段失败，则确认是 Runner 级别的基础设施问题。

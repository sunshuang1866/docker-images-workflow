# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, eulerpublisher, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

Check 结果表为空：
```
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI [Check] 阶段，测试基础设施内部
- 失败原因: CI runner 上的 `eulerpublisher` 容器测试框架中，`common_funs.sh`（路径 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`）在第 13 行尝试 `source` 加载 `shunit2` shell 单元测试框架，但该文件在 runner 上不存在，导致所有 Check 项无法执行，Check 阶段判定为失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 具体证据如下：
1. PR 仅新增了 `Others/httpd/2.4.66/24.03-lts-sp4/` 下的 Dockerfile 和 `httpd-foreground` 入口脚本，以及更新了 README、`image-info.yml`、`meta.yml` 等元数据文件，均为标准的新 OS 版本支持流程。
2. Docker 镜像构建阶段（Build + Push）**已成功完成**：所有 7 个 RUN 步骤（#0 到 #13）均正常退出，镜像导出和推送也成功（`sha256:b38237a...`）。
3. 失败发生在 CI 流水线的 [Check] 阶段——该阶段由 `eulerpublisher` 工具负责运行容器功能验证测试，`shunit2` 缺失是该工具在 CI runner 上的部署问题，与本次 PR 的任何变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。`shunit2` 是标准的 Shell 单元测试库，通常通过包管理器安装（如 `dnf install shunit2`）或手动部署到 `eulerpublisher` 期望的路径下。此为 CI 基础设施维护操作，Code Fixer 无需处理。

## 需要进一步确认的点
1. 是否同一 CI runner 上其他使用 `eulerpublisher` Check 阶段的应用镜像也出现相同故障？如果是，则为 runner 级别的环境问题。
2. `shunit2` 在 openEuler 24.03-LTS-SP4 的软件源中是否已被移除或改名？需确认包名和可用性。
3. `eulerpublisher` 工具的版本是否为此次 CI 运行所使用的最新版本——`common_funs.sh` 中 `shunit2` 的加载路径是否随工具版本更新而变化？

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed, eulerpublisher

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 流水线的 [Check] 阶段执行容器镜像测试时，`common_funs.sh` 脚本尝试通过 `. shunit2` 命令加载 `shunit2` shell 测试框架，但该框架未安装在 CI runner 上，导致测试根本无法启动（Check Results 表格为空），最终 CI 流水线标记为 FAILURE。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、httpd-foreground 脚本，并更新了 meta.yml、README.md、image-info.yml 等元数据文件。Docker 镜像构建全部 7 个 RUN 步骤均成功完成（`#10 DONE 41.6s`、`#11 DONE 0.1s` 等），[Build] 和 [Push] 阶段也均标记为 `finished`。失败发生在随后的 CI 自有的容器测试框架初始化阶段，属于 CI 基础设施问题，与本次 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` shell 测试框架。`shunit2` 是一个标准的 shell 单元测试库，应通过包管理器（如 `dnf install shunit2` 或 `apt install shunit2`）安装到 CI runner 的全局路径中（如 `/usr/local/etc/eulerpublisher/tests/container/` 或系统 PATH 中），使 `common_funs.sh:13` 的 `source` 命令能够找到该文件。这是纯 CI 基础设施运维操作，与代码无关。

## 需要进一步确认的点
- 确认该 CI runner 上其他镜像的 [Check] 阶段是否同样失败：如果其他镜像也因同一原因失败，说明是 runner 环境整体缺少 `shunit2`；如果仅该 PR 失败，需确认是否因 runner 分配、环境变量或工作目录差异导致 `shunit2` 路径不可访问。
- 确认 `shunit2` 在 openEuler 仓库中的包名（可能是 `shunit2` 或 `shunit`），以及安装后的实际路径是否与 `common_funs.sh` 中 `source` 的路径预期一致。

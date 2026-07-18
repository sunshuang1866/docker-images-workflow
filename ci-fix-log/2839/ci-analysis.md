# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试工具缺失
- 新模式症状关键词: shunit2, No such file or directory, [Check] test failed, common_funs.sh

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI 编排工具 eulerpublisher 的 `[Check]` 测试阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` Shell 单元测试框架，导致测试脚本在 source 阶段崩溃，Check Items 表格为空（零项测试被执行）

### 与 PR 变更的关联
**与 PR 无关**。证据如下：
1. Docker 镜像构建阶段全部成功完成：`#8 DONE 268.4s`（编译安装 PostgreSQL）、`#9 DONE 0.1s`（COPY entrypoint.sh）、`#10 DONE 0.1s`（chmod）、`#11 DONE 58.0s`（导出并推送镜像）。
2. 日志中 `[Build] finished` 和 `[Push] finished` 均正常打印。
3. 失败仅发生在 eulerpublisher 的 `[Check]` 测试执行阶段——`common_funs.sh` 尝试 `source` 或调用 `shunit2` 时找不到该命令（`No such file or directory`），导致整个测试套件在未执行任何实际容器检测的情况下崩溃。
4. Check Items 表格完全为空，说明没有任何容器层面的测试被执行，报错发生在测试框架自身的初始化阶段。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` 包。需要在 CI runner 镜像或测试环境中安装 `shunit2`（如在 openEuler 上可通过 `dnf install shunit2` 或从 GitHub releases 下载安装）。此修复应在 CI 基础设施层面完成，**无需修改 PR 中的任何代码文件**。

### 方向 2（置信度: 低，备选）
如果 `shunit2` 实际上已安装但不在 `PATH` 中，或 `common_funs.sh` 对 `shunit2` 路径的引用方式有误，则需要修正 `eulerpublisher` 工具包中 `common_funs.sh` 的 `shunit2` 引用路径。但此可能性较低，标准安装通常会将 `shunit2` 放入 `/usr/bin/`。

## 需要进一步确认的点
1. 确认 CI runner 节点上 `shunit2` 是否已安装：`which shunit2` 或 `dnf list installed | grep shunit2`。
2. 确认 `common_funs.sh` 第 13 行期望的 `shunit2` 调用方式（是直接命令调用还是 source 文件路径），以判断是缺少二进制还是缺少库文件。
3. 确认同类已成功通过 `[Check]` 阶段的 PR（如 postgres 17.6-oe2403sp2）是否在同一批 CI runner 上运行，以排除 runner 环境漂移。

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 主机环境（`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 第 13 行）
- 失败原因: CI 运行时环境缺少 `shunit2`（Shell 单元测试框架），导致 `common_funs.sh` 无法 `.`（source）该框架，整个 Check 阶段初始化失败，Check Items 表格完全为空（无任何测试结果输出）

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增了一个 Dockerfile（`Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`）及配套文件。Docker 镜像构建（7/7 个步骤全部成功）、推送均已完成：
```
#10 DONE 41.6s   （configure + make + make install 完成）
#11 DONE 0.1s    （groupadd / useradd / sed 配置完成）
#12 DONE 0.0s    （COPY httpd-foreground 完成）
#13 DONE 0.1s    （chmod 完成）
#14 DONE 31.3s   （镜像导出并成功推送）
```
失败发生在构建与推送之后、`eulerpublisher` 工具执行 `[Check]` 阶段时 —— 这是由于 CI Runner 主机环境中 `shunit2` 测试框架未安装或路径配置不当所致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 节点上安装 `shunit2` 包。代码仓库无需任何修改，Dockerfile 本身质量无问题（构建成功、推送成功）。该 CI Runner 为本次构建调度的特定节点，需运维确认该节点上 `shunit2` 框架是否缺失，或是否存在多节点环境中部分节点未安装 `shunit2` 的不一致情况。

## 需要进一步确认的点
- 该 CI Runner 节点（执行本次 Jenkins job 的节点）上 `shunit2` 是否已安装；如已安装，确认其安装路径是否在脚本预期的搜索路径（如 `$PATH` 或 `source` 查找路径）内
- 同一镜像仓库中其他镜像（如已有的 `2.4.66-oe2403sp2`）的 Check 阶段是否能正常执行 —— 若其他镜像也因同样原因失败，说明是全局 CI 环境问题；若仅本次失败，则可能是特定调度节点的局部环境缺陷

## 修复验证要求
无需对代码仓库进行修复。若运维侧在 CI Runner 上安装 `shunit2` 后重新触发构建，验证要点：
- Check 阶段应正常初始化，`Check Items` 表格应出现至少一条测试结果行（正常行为包含容器启动测试等）
- 整个过程应以 `Finished: SUCCESS` 结束

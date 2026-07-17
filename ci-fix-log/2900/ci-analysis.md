# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试依赖缺失
- 新模式症状关键词: shunit2: file not found, Check test failed, common_funs.sh, eulerpublisher

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 环境中的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2` Shell 单元测试框架包，`common_funs.sh` 第 13 行尝试 `source` 加载 `shunit2` 时因文件不存在而失败，导致整个测试检查阶段直接失败，test 结果表格为空

### 与 PR 变更的关联
**与 PR 变更无关。** 证据如下：

1. **Docker 构建全部成功**：日志中 `#10 DONE 41.6s` 表明 `make && make install` 步骤正常完成；`#11 DONE 0.1s` 表明 `groupadd`/`useradd` 及 `sed` 配置步骤正常完成；`#12 DONE 0.0s` 和 `#13 DONE 0.1s` 表明 COPY 和 chmod 步骤正常完成
2. **镜像推送成功**：日志明确输出 `[Build] finished` 和 `[Push] finished`
3. **失败点明确在 CI 测试框架层**：`[Check]` 阶段因 Runner 上 `shunit2` 缺失而崩溃，`Check` 结果表为空（表中没有任何 `Check Items` 条目），证明没有任何业务测试被实际执行
4. 所有 7 个 Dockerfile 构建步骤（`#9` 到 `#13`）均以 `DONE` 状态完成

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` 包。`shunit2` 是 Shell 单元测试框架，在 openEuler 上可通过 `dnf install shunit2` 或等效方式安装。此问题属于 CI 基础设施配置缺失，无需对 PR 中的 Dockerfile 或任何代码文件做任何修改。

## 需要进一步确认的点
- 确认 CI Runner（执行 Check 阶段的具体节点）上 `shunit2` 包是否已被意外卸载或从未安装
- 确认该节点上是否还有其他镜像（如同仓库内其他 httpd 版本的 SP4 Dockerfile）在 Check 阶段也因同样原因失败，以判断这是个别 Runner 节点问题还是全局 CI 环境变更导致

## 修复验证要求
无需对 PR 代码进行修复验证。此错误为 CI 基础设施问题（`infra-error`），与 PR 变更完全无关。若需重新触发 CI 验证，需先确保 Runner 环境中已安装 `shunit2` 包。

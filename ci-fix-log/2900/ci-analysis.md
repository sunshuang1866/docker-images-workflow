# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Check阶段缺shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, line 13, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 `common_funs.sh` 脚本在第 13 行尝试 source `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在当前 CI runner 上，导致 Check 阶段无法启动任何测试用例，测试结果表为空，最终标记为 `[Check] test failed`。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的新增 Dockerfile 构建完全成功：
- `#10 DONE 41.6s` — httpd 2.4.66 编译安装成功
- `#11 DONE 0.1s` — 用户/组创建及配置修改成功
- `#12 DONE 0.0s` — httpd-foreground 脚本复制成功
- `#13 DONE 0.1s` — 权限设置成功
- 镜像已成功构建并推送：`[Build] finished` / `[Push] finished`

Docker 镜像本身没有任何构建错误。失败仅发生在 CI 后置 Check 阶段，因 CI runner 缺少 `shunit2` 依赖导致测试无法执行。

## 修复方向

### 方向 1（置信度: 高）
**在 CI runner 上安装 `shunit2` 包。** 这是 CI 基础设施问题，需要在相关 CI runner 节点上安装 `shunit2` 测试框架（在 openEuler 上通常通过 `dnf install shunit2` 或 `pip install shunit2` 安装）。与 PR 代码变更无关，无需修改 Dockerfile 或任何仓库文件。

### 方向 2（置信度: 低）
**CI runner 调度问题。** 如果 `shunit2` 仅在部分 runner 节点上缺失，可能是该 PR 被调度到了一个未充分配置的 runner 上。可尝试重试构建，确认是否为偶发的节点问题。

## 需要进一步确认的点
1. 确认 CI 环境中 `shunit2` 的安装方式和预期路径（是系统包还是 Python 包，或是由 eulerpublisher 自带）
2. 确认该 CI runner 节点上 `shunit2` 是否曾经可用（是否存在近期的 CI 环境变更导致其丢失）
3. 确认此失败是特定于该 runner 还是所有 runner 都存在（可通过查看同一时期其他 PR 的 Check 阶段是否也失败来判断）
4. 虽然 Docker 镜像构建成功，但需确认镜像内容是否完整正确（如 httpd 服务能否正常启动）

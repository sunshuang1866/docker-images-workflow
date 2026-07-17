# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI检查工具缺失
- 新模式症状关键词: shunit2, No such file or directory, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI 工具脚本，非 PR 代码）
- 失败原因: CI runner 环境中缺少 `shunit2` Shell 单元测试框架，导致 [Check] 阶段的镜像功能测试脚本无法加载执行，测试结果表为空，整个 check 阶段失败

### 与 PR 变更的关联
**与 PR 代码变更无关。** Docker 镜像构建和推送阶段均已成功完成：
- 编译阶段：PostgreSQL 17.6 源码编译完全通过（`#8 DONE 268.4s`，所有 `make install` 目标成功）
- 导出/推送阶段：镜像成功导出并推送到 registry（`[Build] finished`，`[Push] finished`，sha256 记录完整）

失败仅发生在构建完成后的 [Check] 阶段，该阶段由 `eulerpublisher` 工具驱动，尝试运行 `shunit2` 对镜像进行容器级功能验证，但因 shunit2 在 CI runner 上缺失而崩溃。

Dockerfile 中存在的两个 `LegacyKeyValueFormat` Docker 警告（第 26、30 行的 ENV 格式）为非致命性 lint 提示，不影响构建结果。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境（或 `eulerpublisher` 容器测试工具包）中安装 `shunit2` Shell 测试框架。这是 CI 基础设施问题，code-fixer 无需对 PR 中的 Dockerfile、entrypoint.sh、meta.yml 等文件做任何修改。

## 需要进一步确认的点
- 确认该 CI runner 是否在其他 job 中也出现 `shunit2: No such file or directory` 错误，以判断是全局性问题还是本 job 专属问题
- 如果 shunit2 在 CI runner 上之前可用但现在缺失，需确认 CI 环境最近是否有变更（如容器镜像更新、软件包清理等）
- 由于 check 阶段完全未执行（结果表为空），无法确认 PostgreSQL 17.6 镜像在 openEuler 24.03-LTS-SP4 上的实际运行行为是否正确，建议 CI 环境修复后重新触发构建以完成完整的 check 验证

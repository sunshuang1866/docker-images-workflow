# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, check test failed, eulerpublisher

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
- 失败位置: CI [Check] 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境缺少 `shunit2` shell 测试框架，`eulerpublisher` 的 check 脚本在 `source` shunit2 时失败（`.: shunit2: file not found`），导致所有 check 项均未执行，直接判定测试失败

### 与 PR 变更的关联
**与 PR 完全无关**。PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和相关元数据文件。Docker 镜像构建阶段全部成功：
- 7/7 构建步骤均 DONE（`#10 DONE 41.6s`, `#11 DONE 0.1s`, `#12 DONE 0.0s`, `#13 DONE 0.1s`）
- 镜像成功导出并推送（`[Build] finished`, `[Push] finished`, `#14 DONE 31.3s`）
- 失败发生在构建完成后的 CI 基础设施测试阶段，与 Dockerfile 内容无关

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` 包。需要在 CI 节点上安装 `shunit2`（可通过 `dnf install shunit2` 或从源码安装），使 `eulerpublisher` 的 check 脚本能正常加载测试框架。此问题需要 CI 运维侧处理，非 PR 作者可修复。

## 需要进一步确认的点
- 确认 CI runner 节点上 `shunit2` 的预期安装路径是否为 `/usr/share/shunit2/shunit2`（常见默认路径）
- 确认该 CI runner 是仅有此 job 缺少 shunit2，还是所有 check job 都有此问题（若是后者，说明 CI 环境镜像需更新以包含 shunit2 依赖）
- 若其他镜像的 check 能正常执行，则需检查 shunit2 在 `common_funs.sh` 中的 source 路径是否因新基础镜像环境而改变

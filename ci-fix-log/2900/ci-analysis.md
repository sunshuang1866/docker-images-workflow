# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

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
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行器上未安装 `shunit2` shell 测试框架，导致 `eulerpublisher` 的 `[Check]` 阶段无法执行容器镜像验证测试，所有测试项为空（表格无条目）。

### 与 PR 变更的关联
与 PR 变更**无关**。Docker 镜像的构建（`[Build]`）和推送（`[Push]`）阶段均已完成：
- `#10 DONE 41.6s` — make && make install 成功
- `#11~#13 DONE` — groupadd/useradd、sed 配置、COPY、chmod 均成功
- `#14 exporting layers 11.7s done` — 镜像导出成功
- `#14 pushing layers 15.8s done` — 镜像推送成功
- `[Build] finished` / `[Push] finished` — 日志明确标记成功

失败仅发生在 CI 工具链的 `[Check]` 后处理阶段，因 `shunit2` 依赖缺失而无法运行容器验证测试。PR 新增的 Dockerfile 和 `httpd-foreground` 脚本结构正确、构建通过。

## 修复方向

### 方向 1（置信度: 高）
在 CI 运行器上安装 `shunit2` 测试框架包，确保 `eulerpublisher` 的 `[Check]` 阶段能够正常加载 `common_funs.sh` 引用的 `shunit2` 库。此修复属于 CI 基础设施配置变更，不涉及 PR 代码修改。

## 需要进一步确认的点
- 确认该 CI runner 是否本应预装 `shunit2`（如是，排查环境变更导致依赖丢失的原因）
- 确认 openEuler 24.03-LTS-SP4 的容器测试套件是否需要额外适配（当前测试脚本与 SP2/SP3 共用同一套 `common_funs.sh`，理论上无需适配）
- 如果其他同样使用 `[Check]` 阶段的 PR 近期也出现相同错误，可确认为 CI 环境全局性问题

# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check, test failed, eulerpublisher

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` Shell 测试框架，导致 eulerpublisher 容器的 [Check] 阶段测试脚本无法 sourc `shunit2` 库而失败。Docker 镜像的构建和推送本身均已完成（422 个编译目标全部链接成功，镜像推送到 docker.io 成功）。

### 与 PR 变更的关联
PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 named.conf）、README 条目、image-info.yml 条目和 meta.yml 条目。Docker 镜像构建完全成功，所有编译任务（libisc、libdns、libns、libisccc、libisccfg 库及 named 等全部工具）均正常完成。失败发生在构建后的 CI 基础设施层测试阶段，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 aarch64 CI runner 上安装 `shunit2` 包（openEuler 上可能为 `shunit2`），使 `common_funs.sh` 中的 `. shunit2` 能正确找到并加载测试框架。此操作需由 CI 管理员在 runner 镜像/环境中执行，非 PR 提交者无责修复。

## 需要进一步确认的点
- 同一 PR 的 x86_64 架构构建 job 是否也因相同原因失败，还是仅 aarch64 架构存在此问题（当前日志仅覆盖 aarch64 job）。
- `shunit2` 在 openEuler 24.03-LTS-SP4 仓库中的确切包名（可能为 `shunit2` 或 `shunit`），确认后由 CI 管理员补充安装。

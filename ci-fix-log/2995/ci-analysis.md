# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: `bad interpreter`, `/bin/sh^M`, `CRLF`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具包中的 bwa 镜像测试脚本）
- 失败原因: eulerpublisher 软件包中的 `bwa_test.sh` 测试脚本使用了 Windows 风格的 CRLF 换行符（`\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的 `\r` 被当作解释器名称的一部分，Linux 系统找不到 `/bin/sh^M` 解释器，脚本无法执行，CI [Check] 阶段失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 证据如下：
1. Docker 镜像**构建成功**：所有步骤（yum 安装依赖 → 下载源码 → 编译 bwa → 安装 → 清理）均顺利完成，镜像已成功推送至仓库（`#8 DONE 8.4s`）
2. [Build] 和 [Push] 阶段均输出 `finished`，仅在 [Check] 阶段失败
3. 失败脚本 `bwa_test.sh` 位于 eulerpublisher 系统安装路径（`/usr/etc/eulerpublisher/tests/container/app/`），属于 CI 基础设施，非 PR 提交文件
4. PR 仅新增/修改了 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml），均与构建流程相关，不涉及测试脚本

## 修复方向

### 方向 1（置信度: 高）
将 eulerpublisher 包中 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新安装/部署 eulerpublisher 包。此修复需由 CI 基础设施维护者执行，**PR 作者无需操作**。

### 方向 2（置信度: 低）
若 bwa_test.sh 实际来源于 eulerpublisher 的上游 Git 仓库（CI 日志显示 `Cloning into 'eulerpublisher'...`），需要在上游仓库中将该文件转为 LF 换行符并提交（可能需配合 `.gitattributes` 设置 `*.sh text eol=lf`），CI 节点重新拉取后即可生效。

## 需要进一步确认的点
1. 确认 `bwa_test.sh` 的准确来源：是从 eulerpublisher RPM/pip 包安装的，还是从上游 Git 仓库克隆后部署的
2. 确认是仅 bwa_test.sh 一个文件存在 CRLF，还是 eulerpublisher 中多个测试脚本均受影响
3. 排查 eulerpublisher 的打包/发布流程中是何环节引入了 CRLF（可能是在 Windows 环境编辑后提交）

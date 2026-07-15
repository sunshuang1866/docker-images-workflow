# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, CRLF, eulerpublisher, test

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 测试套件中的静态脚本）
- 失败原因: CI 基础设施中 eulerpublisher 包的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF），导致 shebang 行被解析为 `#!/bin/sh^M`，系统找不到名为 `/bin/sh^M` 的解释器。该文件位于 CI runner 已安装的 eulerpublisher Python 包内，属于系统级别文件，与本次 PR 变更无关。

### 日志中构建阶段的关键事实
1. **Docker 构建完全成功** — `#7 [2/2] RUN yum ...` 步骤从依赖安装、源码下载（curl 成功获取 v0.7.18.tar.gz）、编译（make 无 fatal error，仅两个 set-but-not-used warning）、到卸载构建工具，全程通过（199.0s）。
2. **镜像导出与推送成功** — `#8 exporting to image` 正常完成，manifest 已推送至目标 registry。
3. **CI 日志的 BUILD/PUSH 阶段均以 `[Build] finished` / `[Push] finished` 确认成功。**
4. **失败仅发生在 eulerpublisher 的 [Check] 阶段**，该阶段调用系统预装的 `bwa_test.sh` 执行镜像健康检查时，因脚本自身含 CRLF 而无法启动。

### 与 PR 变更的关联
**无关联。** 本次 PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 并更新了 `meta.yml`、`README.md`、`image-info.yml`。这些文件不包含、也不会生成或修改 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`。Docker 镜像的构建和编译阶段已完全成功，证明 PR 中的 Dockerfile 本身没有问题。失败的 [Check] 阶段使用的测试脚本属于 CI runner 上已安装的 eulerpublisher 包的内容，其 CRLF 问题与 PR 变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需修复 eulerpublisher 包中 `bwa_test.sh` 的行尾格式：将 CRLF 转换为 LF。可以通过 `dos2unix` 命令处理该文件后重新打包/部署 eulerpublisher，或在该包的上游仓库中将 `bwa_test.sh` 的 Git 属性配置为 `text eol=lf` 后重新提交。

### 方向 2（置信度: 低）
如果 eulerpublisher 的测试脚本是从仓库中动态加载的（而非包预装），则需检查仓库中是否存在一个含 CRLF 的 `bwa_test.sh` 副本。但从日志路径 `/etc/eulerpublisher/tests/container/app/` 和 CI 流程（先安装 eulerpublisher 包再运行 check）来看，该脚本属于系统级安装，概率极低。

## 需要进一步确认的点
1. 确认 eulerpublisher Python 包中 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 的当前行尾格式：在 CI runner 上执行 `file /etc/eulerpublisher/tests/container/app/bwa_test.sh` 或 `od -c` 查看是否包含 `\r`。
2. 如果该脚本确实来自 eulerpublisher 包，向 eulerpublisher 维护团队提报该文件存在 CRLF 行尾问题。
3. 验证同样使用 eulerpublisher [Check] 阶段的其他应用的测试脚本是否也存在 CRLF 问题（非必须，但有助于判断影响范围）。

## 修复验证要求
不适用。本失败为 CI 基础设施问题（eulerpublisher 包内测试脚本的 CRLF 格式），修复不属于本 PR 的 Dockerfile 层面。Code-fixer 无需对本 PR 的 Dockerfile 或元数据文件做任何更改。

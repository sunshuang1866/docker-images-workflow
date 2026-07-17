# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具内置测试脚本）
- 失败原因: 测试脚本 `bwa_test.sh` 的第一行（shebang）使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致 Linux 内核将 shebang 解释器路径解析为 `/bin/sh\r`（而非 `/bin/sh`），报 `bad interpreter: No such file or directory`，脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增 Dockerfile 和更新元数据文件（README.md、image-info.yml、meta.yml），所有文件均使用 Unix 换行符（LF）。Docker 镜像构建和推送均已成功完成（日志中可见 `[Build] finished` 和 `[Push] finished`）。失败发生在 CI 工具内置的测试脚本中，该脚本属于 eulerpublisher 安装包，不在本仓库内。

## 修复方向

### 方向 1（置信度: 高）
该失败为 CI 基础设施问题，**code-fixer 无需处理**。应由 CI 运维人员检查 eulerpublisher 安装包中 `tests/container/app/bwa_test.sh` 文件的换行符格式，使用 `dos2unix` 或 `sed -i 's/\r$//'` 将 CRLF 转换为 LF 后重新部署。

## 需要进一步确认的点
1. eulerpublisher 包中是否还有其他测试脚本存在同样的 CRLF 换行符问题，可能影响其他镜像的 CI 检查。
2. aarch64 架构的构建 job 日志未提供，无法确认 aarch64 侧是否也存在相同问题或已通过。当前仅看到 x86_64 的 job 输出。
3. 该 CRLF 问题是否为本轮 CI 运行中某个步骤意外引入（如 git clone 时 `core.autocrlf` 配置不当），而非 eulerpublisher 包本身的问题；需复查 CI runner 的 git 全局配置和 eulerpublisher 包的安装来源。

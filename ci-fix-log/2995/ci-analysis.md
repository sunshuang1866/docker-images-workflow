# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: `/bin/sh^M`, `bad interpreter`, `No such file or directory`, `carriage return`, `eulerpublisher`, `test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher 工具内置测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（即 `/usr/local/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: CI 工具 `eulerpublisher` 中的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF），shebang 行 `#!/bin/sh` 末尾带有回车符 `\r`（日志中显示为 `^M`），导致系统尝试将 `/bin/sh\r` 作为解释器执行，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联

**PR 变更与失败无关。** 证据如下：

1. **Docker 构建完全成功**：日志显示 BWA 编译通过（所有 `.c` 文件编译成功，`bwa` 二进制正常链接），镜像构建成功（`#7 DONE 199.0s`），镜像导出并推送成功（`#8 DONE 8.4s`），`[Build] finished` 和 `[Push] finished` 均在 INFO 级别盖章。
2. **失败发生在 CI 自身的后置检查阶段**：`[Check]` 阶段调用的是 eulerpublisher 包自带的测试脚本，该脚本不在 PR diff 的任何文件中，不由本次 PR 管理或控制。
3. **PR diff 仅涉及 4 个文件**：新增 Dockerfile（纯 LF 格式）、修改 README.md、image-info.yml、meta.yml，均不涉及任何测试脚本或 CI 配置。

## 修复方向

### 方向 1（置信度: 高）
这是 eulerpublisher CI 工具包中 `bwa_test.sh` 文件的 CRLF 行尾问题，与 PR 代码无关。需要 eulerpublisher 仓库的维护者将 `bwa_test.sh`（以及可能同批次引入的其他测试脚本）的行尾格式从 CRLF 转换为 LF，可通过 `dos2unix` 或 `sed -i 's/\r$//'` 完成。

### 方向 2（可选）
如果 `bwa_test.sh` 是 eulerpublisher 为了支持 bwa 镜像检查而**新创建的**测试脚本，并且创建方式导致其继承了 CRLF 行尾（例如在 Windows 环境编辑或通过特定 git 配置克隆），则需要在 eulerpublisher 仓库中修复该文件后，重新部署到 CI runner。

## 需要进一步确认的点
1. 确认 `bwa_test.sh` 在 eulerpublisher 仓库中的行尾格式，以及该文件是否为近期新增。
2. 排查 eulerpublisher 仓库中是否还有其他测试脚本（`*_test.sh`）存在同样的 CRLF 行尾问题。
3. 确认 CI 环境中 eulerpublisher 的部署/更新流程，确保修复后的脚本能及时同步到所有 runner 节点。

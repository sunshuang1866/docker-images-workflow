# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，调用 `eulerpublisher` 内置测试脚本 `bwa_test.sh` 时
- 失败原因: CI 基础设施 `eulerpublisher` 包中的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用了 Windows 风格的换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾带有不可见字符 `\r`（日志中显示为 `^M`），内核尝试查找解释器 `/bin/sh\r` 失败，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
- **Docker 镜像构建完全成功**：日志显示 `yum install` → `curl` 下载 bwa 源码 → `make` 编译 → 二进制安装 → `yum remove` 清理 → 镜像导出与推送均顺利完成（`#7 DONE 199.0s`，`[Build] finished`，`[Push] finished`）。
- PR 新增的 Dockerfile 自身无任何构建问题，Docker 层全部执行成功，镜像已成功推送至 registry。
- 失败仅发生在 CI 流水线的 **[Check] 测试阶段**，由 CI 基础设施（`eulerpublisher` 包）的测试脚本 `bwa_test.sh` 自身格式问题导致，**与 PR 的代码变更无关**。

## 修复方向

### 方向 1（置信度: 高）
该问题属于 CI 基础设施缺陷，**无需对 PR 的 Dockerfile 或任何仓库文件进行修改**。需要 CI 平台/`eulerpublisher` 包的维护者修复 `bwa_test.sh` 文件的换行符格式（将 CRLF 转换为 LF，如使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该脚本）。

### 方向 2（置信度: 低）
若该测试脚本是从另一个 Git 仓库（`eulerpublisher` 源码仓库）在 CI 运行时 `git clone` 获取的，需检查该仓库中 `tests/container/app/bwa_test.sh` 的换行符格式，必要时在该仓库中修正后重新发布 `eulerpublisher` 包。但从日志路径 `/usr/lib64/python3.9/../../etc/eulerpublisher/...` 看，该脚本通过 Python 包安装，更可能是包发布时的格式问题。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 的实际换行符格式（在 CI runner 上执行 `file /etc/eulerpublisher/tests/container/app/bwa_test.sh` 或 `od -c` 查看）。
2. 检查 `eulerpublisher` 源码仓库中该测试脚本是否以 CRLF 格式提交，若是则需在源头修复。
3. 确认其他应用镜像（如已有 bwa 的 22.03-lts-sp3 版本）的 check 测试是否也使用同一脚本，若已通过则说明该脚本可能近期被引入/更新时引入了 CRLF 问题。

# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于 CI 基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无。此失败为 CI 工具链 `eulerpublisher` 内置测试脚本 `bwa_test.sh` 的 CRLF 行尾编码问题，不在本仓库代码范围内。

## 修复逻辑
CI 日志显示 Docker 镜像构建（`#7 DONE 199.0s`）和推送（`[Push] finished`）均完全成功。失败发生在构建之后的 `[Check]` 阶段，错误为：

```
/bin/sh: /usr/lib64/.../bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
```

根因是 `eulerpublisher` 工具链中的 `tests/container/app/bwa_test.sh` 脚本使用了 Windows 风格的 CRLF 行尾，导致 shebang `#!/bin/sh` 被解析为 `#!/bin/sh\r`，Linux 系统找不到该解释器路径。

此问题应由 CI 基础设施维护者修复 `eulerpublisher` 包/仓库中的 `bwa_test.sh` 文件（将行尾从 CRLF 转换为 LF），或检查该仓库的 `.gitattributes` 配置。PR 提交的 Dockerfile、README.md、image-info.yml、meta.yml 四个文件均不涉及任何行尾或脚本问题。

## 潜在风险
无。未对代码做任何修改。
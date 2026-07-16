# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, test failed, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher 包内 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具自带测试脚本，非 PR 文件）
- 失败原因: `bwa_test.sh` 文件使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的 `\r`（显示为 `^M`）被当作解释器名称的一部分，系统无法找到 `/bin/sh\r` 这个可执行文件，脚本执行失败

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增了 bwa 0.7.18 在 openEuler 24.03-lts-sp4 上的 Dockerfile，以及相应的 README、image-info.yml、meta.yml 更新。Docker 镜像的构建和推送均已完成并成功：

- `#7 DONE 199.0s` — Docker 构建成功
- `[Build] finished` — 构建阶段完成
- `[Push] finished` — 推送阶段完成

失败仅发生在 CI 流水线的 `[Check]` 阶段，原因是 eulerpublisher CI 工具包自带的 `bwa_test.sh` 测试脚本存在 CRLF 换行符问题，与该 PR 的任何变更无关。

## 修复方向

### 方向 1（置信度: 高）
通知 eulerpublisher 包的维护者修复 `tests/container/app/bwa_test.sh` 文件的换行符：将 CRLF (`\r\n`) 转换为 LF (`\n`)。可使用 `dos2unix` 或在 git 仓库中配置 `.gitattributes` 强制该文件使用 LF 换行。修复后 PR 重新触发 CI 即可通过 Check 阶段。

## 需要进一步确认的点

1. 该 PR 的 `meta.yml` 中新增条目未设置 `arch: x86_64` 约束（参考模式30/31）。如果 CI 也调度到 aarch64 runner 上构建，需确认 aarch64 构建是否成功（当前日志仅为 x86-64 job）。bwa 源码本身支持 aarch64 编译，但若 aarch64 job 日志中出现架构相关问题，需对应补充 `arch` 约束或修复编译问题。
2. Dockerfile 中 `RUN` 指令的 `make -j "$(nproc)" && \ `（反斜杠后有空格）虽未导致构建失败，但属于不规范的 shell 行续写写法，建议修正为 `&& \`（反斜杠后直接换行，无多余空格）。

# 修复摘要

## 修复的问题
Dockerfile 第 36 行 `import re` 被 Docker 解析器误认为顶层指令，导致 `dockerfile parse error on line 36: unknown instruction: import` 构建错误。

## 修改的文件
- `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`: 将 `python3 -c '...'` 中的多行 Python 内联脚本改为通过 `printf '%b' '...' | python3 -` 方式传递，使 Python 代码保持在单行 Dockerfile 指令内，消除了解析歧义。

## 修复逻辑
根因：原 Dockerfile 第 35 行 `python3 -c '` 以单引号开启 Python 代码块后，第 36 行 `import re` 作为独立行出现。由于没有 `\` 续行符，Docker 解析器将 `import re` 视为新的 Dockerfile 指令，而 `import` 不是合法的 Dockerfile 指令，导致解析失败。

修复方案：使用 `printf '%b' '...' | python3 -` 替代 `python3 -c '...'`。`printf '%b'` 会将参数中的 `\n` 转义序列解释为实际换行符，从而将完整的 Python 源代码通过标准输入传递给 `python3 -`。所有 Python 代码封装在 `printf '%b' '...'` 的单个参数中，作为一条完整的 shell 命令嵌入 RUN 指令。

Python 代码功能保持不变：对 ovirt-engine 源码中的 `LocalizedMessageHelperTest.java` 中的三个测试方法（`testForEnglish`、`testForNonTranslatedLanguage`、`testForNotDefaultLanguage`）通过正则表达式添加注释禁用标记。

已验证：通过 `printf '%b' '...' | python3 -` 语法在本地 bash 环境中测试，Python 代码语法正确，正则替换功能正常。

## 潜在风险
- `printf '%b'` 对 `\(`、`\)`、`\{`、`\}` 等非标准转义序列的行为虽在 bash/dash 中已验证为直接透传，但 POSIX 标准对此类序列定义为"未定义行为"。若 CI 构建环境使用非标准 shell（非 bash/dash），需验证兼容性。
- 其他文件（`Cloud/ovirt-engine/README.md`、`Cloud/ovirt-engine/doc/image-info.yml`、`Cloud/ovirt-engine/meta.yml`）无需修改。
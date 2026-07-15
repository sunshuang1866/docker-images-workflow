# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Conan hooks 配置语法错误
- 新模式症状关键词: You can't set a full section, please specify a section.key=value, conan config set hooks

## 根因分析

### 直接错误
```
#12 28.95 ERROR: You can't set a full section, please specify a section.key=value
#12 ERROR: process "/bin/sh -c curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain=1.73 -y &&     pip install conan==1.61.0 &&     mkdir -p /root/.conan/hooks &&     printf ...     > /root/.conan/hooks/bzip2_source_fix.py &&     conan config set hooks=bzip2_source_fix" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`:39
- 失败原因: `conan config set hooks=bzip2_source_fix` 命令语法对 Conan 1.61.0 无效。Conan 的 `conan.conf` 中 `[hooks]` 是一个配置节（section），`conan config set` 命令不允许直接对整个节赋值（即 `hooks=value` 格式），要求使用 `section.key=value` 格式。Dockerfile 中将 hook 名称写成了节级赋值，导致 CLI 拒绝执行。

### 与 PR 变更的关联
PR 新增了 `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`，其第 18-39 行的 `RUN` 指令包含了 Conan hook 的安装和配置步骤。其中 `conan config set hooks=bzip2_source_fix` 语法错误直接导致 Docker 构建在 builder stage 的第 3/4 步失败。该失败完全由此次 PR 引入的新代码触发。

## 修复方向

### 方向 1（置信度: 高）
将 `conan config set hooks=bzip2_source_fix` 替换为直接向 `/root/.conan/conan.conf` 写入 hook 配置的方式，而不是通过 `conan config set` 命令。Conan 1.61.0 的 hooks 配置在 `conan.conf` 中以 `[hooks]` 节下的列表项形式存在，直接追加写入配置文件即可完成 hook 注册。

```dockerfile
# 替换 conan config set hooks=bzip2_source_fix
# 使用 printf 追加写入 conan.conf 的 [hooks] 节
```

## 需要进一步确认的点
无。错误信息和根因明确，无需进一步调查。

## 修复验证要求
无。修复仅涉及 Dockerfile 内 `RUN` 指令中的 Shell 命令调整，不涉及修改正则表达式或 patching 第三方/上游源文件。

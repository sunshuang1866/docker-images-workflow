# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 正则转义导致patch失效
- 新模式症状关键词: Assessing libaio, exit code: 1, getdeps.py, _verify_hash, re.sub, raw string

## 根因分析

### 直接错误
```
#11 333.8 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:18` (RUN 命令)，根因在 `fix_getdeps.py:15-20`
- 失败原因: `fix_getdeps.py` 中用于绕过 `_verify_hash` 的正则表达式使用了 raw string `r'...'` 包裹，其中的 `\n` 被解释为两个字面字符（反斜杠+n），而非换行符，导致正则永远无法匹配源码中的 `_verify_hash` 方法，hash 校验未被实际跳过。当 getdeps 对预置入的 libaio tarball 进行"Assess"时，hash 校验失败导致构建退出码为 1。

### 与 PR 变更的关联
本次 PR 新增了 3 个文件：`Dockerfile`、`fix_getdeps.py`、`libaio-libaio-0.3.113.tar.gz`。其中 `fix_getdeps.py` 的 hash 校验绕过逻辑存在正则编写错误（raw string 中 `\n` 未转义为真正换行符），该错误直接触发了构建失败。libaio 是唯一使用预置 tarball（非 git clone 下载）的依赖，其他依赖（glog、googletest 等）通过 git clone 或 URL 下载且已构建成功，印证了问题集中在 libaio 的 hash 校验环节。

## 修复方向

### 方向 1（置信度: 中）
修复 `fix_getdeps.py` 中正则表达式的换行符问题：将 raw string `r'def _verify_hash\(self\):.*?(?=\n    def )'` 中的 `\n` 替换为真正的换行符（去掉 `r` 前缀并使用 `\\n` 双重转义，或直接在正则中嵌入真实换行符，或改用更可靠的正则写法），确保 `_verify_hash` 方法被正确替换为 `pass`。

### 方向 2（置信度: 低）
如果方向 1 修复后仍然失败，可能 libaio tarball 本身的格式或内容存在问题（如文件名不匹配 getdeps 期望的归档内部结构），需进一步检查 getdeps 对 libaio 的 manifest 配置。

## 需要进一步确认的点
1. **缺失的 stderr 输出**：CI 日志在 `#11 333.8` 行处被截断，`Assessing libaio...` 之后 getdeps 的实际错误输出（stderr）未出现在日志中。需获取完整日志以确认确切的失败信息。
2. **fetcher.py 实际代码**：需确认目标版本 fbthrift（v2026.06.08.00）的 `build/fbcode_builder/getdeps/fetcher.py` 中 `_verify_hash` 方法的实际缩进格式（4 空格缩进 vs tab），以验证修复后的正则是否能准确匹配。
3. **libaio manifest 配置**：需确认 `build/fbcode_builder/getdeps/manifests/libaio` 中定义的归档内部目录结构是否与 `libaio-libaio-0.3.113.tar.gz` 的实际内容一致。

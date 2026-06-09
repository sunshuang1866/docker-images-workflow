# CI 失败分析报告

## 基本信息
- PR: #2558 — fix: fbthrift 2026.06.08.00 (fix #2547)
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 模式22
- 新模式标题: (无 — 匹配已有模式)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
（日志被截断，未捕获到致命错误信息。日志末尾停留在 googletest 安装阶段，最后可见行如下：）
```
#11 335.4 -- Installing: /usr/local/googletest-4jQjSxQTd-HjwRWNCS8vl2kq9IImdZqr5MUHruTRYJs/include/gmock/gmock-more-matchers.h
---（截断）
```

### 根因定位
- 失败位置: 无法定位 — 日志在 getdeps 依赖构建阶段（zstd → boost → glog → gflags → googletest）被截断，尚未进入 fbthrift 本身的编译阶段
- 失败原因: **证据不足，无法确定根因**。实际错误极可能发生在日志截断之后的阶段

### 与 PR 变更的关联
本 PR 是 PR #2547 的修复尝试，核心变更为新增 `fix_getdeps.py`，通过文本替换方式：
1. 将 `"openeuler"` 加入 getdeps 的 RPM 系发行版识别列表（`getdeps_platform.py`）
2. 用正则替换跳过 `fetcher.py` 中 `_verify_hash` 方法，绕过 libaio tarball 的哈希校验

日志截断点与 PR #2547 完全相同（均在 googletest 安装处切断），无法判断 `fix_getdeps.py` 的修复是否生效，也无法确认是否引入了新问题。

日志中多次出现的 `message(SEND_ERROR "Target Boost::XXX already has an imported location...")` 属于 boost b2/cmake 构建系统在安装 cmake 配置文件时的内部警告，通常不构成致命错误（boost 库均成功编译并安装）。

## 修复方向

### 方向 1（置信度: 中）
`fix_getdeps.py` 中 `_verify_hash` 的正则替换仍未正确匹配 `fetcher.py` 中目标方法的完整体。正则 `r'def _verify_hash\(self\):.*?(?=\n(?:    def |class )|\Z)'` 在处理类中最后一个方法时，若该方法体后无同缩进级别的 `def` 或 `class` 行，且文件中存在模块级代码（如 `if __name__ == '__main__':`），正则可能无法正确终止匹配，导致替换静默失败。应改用更稳健的文本处理方式（如按方法边界进行多行匹配的精确替换，或使用 AST / 行级脚本逻辑）。

### 方向 2（置信度: 低）
日志截断前的 `note: failed` 提示 boost exception 库构建失败（`#11 159.5 note: failed. See http://www.boost.org/libs/python/doc/building.html - exception : building`）。虽然该消息以 `note:` 开头且后续 boost 其他库均正常构建，但如果 boost.exception 是 fbthrift 的传递依赖且链接时需要该库，可能在后续 fbthrift 编译阶段触发链接错误。

### 方向 3（置信度: 低）
Dockerfile 中 `ENV PATH=/usr/local/fbthrift/bin:$PATH` 与 getdeps 的 `--install-prefix /usr/local` 可能产生路径不匹配。若 getdeps 将 fbthrift 安装在 `/usr/local/bin` 而非 `/usr/local/fbthrift/bin`，会导致运行时 PATH 无效，但这不会引起构建失败，仅在镜像运行时有影响。

## 需要进一步确认的点
1. 获取 **完整 CI 日志**（未被截断版本），确认日志截断点之后的实际错误信息
2. 验证 `fix_getdeps.py` 在目标 fbthrift 版本（v2026.06.08.00）的 `fetcher.py` 上是否真正完成了 `_verify_hash` 方法的替换——应在脚本中添加替换前后校验（如检查替换后文件内容是否包含 `def _verify_hash(self):\n        pass`）
3. 确认 `getdeps_platform.py` 中的发行版识别字符串在 v2026.06.08.00 版本中是否与 `fix_getdeps.py` 中硬编码的字符串完全一致（含标点符号和括号）
4. 确认 fbthrift v2026.06.08.00 版本的 `getdeps.py` 是否依赖 `boost.exception` 库（若依赖，需在 Dockerfile 中确保 boost 构建时该库编译成功）

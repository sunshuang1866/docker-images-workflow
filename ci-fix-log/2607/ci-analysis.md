# CI 失败分析报告

## PR 信息
- **PR 编号**: #2607
- **PR 描述**: fbthrift 容器镜像升级至版本 2026.06.15.00
- **新增文件**:
  - `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`
  - `fix_getdeps.py`
  - `libaio-libaio-0.3.113.tar.gz`
  - README.md, meta.yml 更新

## Dockerfile 构建流程
1. 从 GitHub 克隆 fbthrift（tag v2026.06.15.00）
2. 预先将 libaio tarball 放入 getdeps 的下载目录
3. 运行 `fix_getdeps.py` 进行补丁：
   - 发行版检测（将 "openeuler" 加入 Fedora 系列列表）
   - fetcher.py 中的哈希校验（将 `_verify_hash` 替换为 `pass`）
4. 运行 `getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift`

## CI 日志分析
- Docker 构建在步骤 [5/5]（构建 fbthrift 的 RUN 命令）失败
- 退出码: 1
- getdeps 构建过程成功下载并构建: ninja, zstd, benchmark, zlib, fmt, boost, fast_float, gflags, glog, googletest
- 到 libaio 评估时，尝试从 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 下载
- 下载返回 HTML（Content-Type: text/html; charset=utf-8），而非 tar.gz
- 仅下载 2238 字节（大小为 "(Unknown)"，无 Content-Length）
- 响应包含 Set-Cookie 头部，提示可能为认证/重定向页面
- 下载失败后构建终止，无后续 libaio 相关输出

## 根因分析
直接错误为从 pagure.io 下载 libaio 失败。PR 的策略是预先放置 tarball 并跳过哈希校验，但未能阻止 getdeps 尝试下载。

两个可能的因素：

1. **主要原因**: pagure.io URL 不可达，或 CI 环境访问时返回错误（返回 HTML 而非二进制文件）。这是一个基础设施/依赖源问题。

2. **次要原因**: `fix_getdeps.py` 中用于修补 `_verify_hash` 的正则表达式可能在 `_verify_hash` 是 Fetcher 类中最后一个方法时匹配失败（正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 要求后面有一个 4 空格缩进的方法定义）。如果正则未匹配，哈希校验未被修补，getdeps 将因哈希不匹配拒绝预先放置的文件，并尝试从失效的 pagure.io URL 重新下载。

预先放置文件的方案可能无效，因为 getdeps 仍会尝试从源 URL 下载，原因可能为：
- 在使用缓存文件前先验证 URL 可达性
- 哈希校验补丁失败（正则问题），导致重新下载
- getdeps 的下载方法在获取前未检查本地文件是否存在

## 失败类型
`dependency-error` — 构建依赖（libaio）无法从其官方源（pagure.io）下载，且绕过方案（预置 tarball + 跳过哈希）未能阻止下载尝试。

## 置信度
中等 — 日志明确显示 pagure.io 下载返回 HTML，但 getdeps 尽管存在预置文件仍尝试下载的确切原因无法仅从日志完全确认。

## 历史模式匹配
**新模式** — 没有现有模式匹配 pagure.io 下载失败 + getdeps 预置文件绕过的组合。

- **新模式标题**: "getdeps预置文件绕过失败"
- **新模式关键词**: pagure.io, libaio, getdeps, text/html, pre-placed, _verify_hash

## 修复方向

### 方向 1（中等置信度）
修补 getdeps 的 `Fetcher` 类下载方法，当本地文件已存在时跳过下载。需要在 `fix_getdeps.py` 中修改 `build/fbcode_builder/getdeps/fetcher.py`，在下载函数之前添加文件存在性检查。

### 方向 2（低置信度）
为 libaio 使用替代下载源。pagure.io URL 在 CI 环境中似乎不可靠。可替换为 GitHub 镜像，或使用多阶段 Docker 构建从已知可靠源提供 libaio。

## 待进一步确认项
- `fix_getdeps.py` 中的正则表达式是否实际匹配 fbthrift v2026.06.15.00 getdeps fetcher.py 中的 `_verify_hash` 方法（如果该方法是类中最后一个方法，正则可能失败）
- getdeps 的下载方法在网络下载前是否有文件存在性检查
- pagure.io 是暂时宕机还是永久阻止 CI 访问

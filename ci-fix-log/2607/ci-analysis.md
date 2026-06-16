# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游归档URL返回HTML非预期内容
- 新模式症状关键词: pagure.io, Content-Type: text/html, tar.gz, Set-Cookie, anubis, anti-bot, libaio, getdeps.py, download

## 根因分析

### 直接错误
```
#11 338.1 Assessing libaio...
#11 338.1 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 338.1 .. 2238 of (Unknown) [Complete in 1.201315 seconds]
#11 338.1 Content-Type: text/html; charset=utf-8
#11 338.1 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 16 Jun 2026 15:43:16 GMT; ...
#11 338.1 Connection: close
#11 338.1 Transfer-Encoding: chunked
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:18` — `getdeps.py build fbthrift` 命令
- 失败原因: `pagure.io` 对 libaio 归档文件的下载请求返回了 HTML 页面（Content-Type: text/html，仅 2238 字节）而非二进制 tar.gz 包，getdeps.py 后续无法解压这个无效文件导致构建退出码 1

## 与 PR 变更的关联

PR 新增了 fbthrift v2026.06.15.00 的 Dockerfile 及配套文件，包括：
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile` — 新的构建文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py` — 补丁脚本
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/libaio-libaio-0.3.113.tar.gz` — 本地备份的 libaio 归档

PR 作者已预见到 libaio 的下载问题，并尝试通过两个手段绕过：
1. 用 `cp` 将本地 `libaio.tar.gz` 预置到 getdeps 的 downloads 目录
2. 通过 `fix_getdeps.py` 修补 `_verify_hash` 为空操作，跳过哈希校验

**但工作不完整**：`fix_getdeps.py` 只修补了哈希校验步骤，未阻止 getdeps.py 从网络重新下载 libaio。预置在 downloads 目录中的本地归档被 getdeps.py 的网络下载覆盖，下载到的 HTML 页面无法解压，导致构建失败。

## 修复方向

### 方向 1（置信度: 高）
在 `fix_getdeps.py` 中增加对 libaio 下载逻辑的修补：让 getdeps.py 在检测到 downloads 目录中已存在 libaio 归档文件时跳过网络下载，直接使用本地文件。可参考 getdeps.py 的下载缓存机制，确保预置的 tar.gz 被正确识别和使用，而非被覆盖。

### 方向 2（置信度: 中）
将 libaio 的来源从 `pagure.io` 替换为其他可靠的镜像源或归档站（如 GitHub releases、软件所镜像等），避免 pagure.io 的 anti-bot 防护拦截 CI 环境请求。但此方向依赖找到与当前版本完全一致的外部源，可能引入额外复杂度。

### 方向 3（置信度: 低）
完全绕过 getdeps.py 的 libaio 自动化构建，改为在 Dockerfile 中手动编译安装 libaio（解压预置的 tar.gz → configure → make → make install），然后在 getdeps.py 调用时使用 `--allow-system-packages` 让 fbthrift 使用系统级别的 libaio。但需确认 fbthrift 的构建系统能否识别系统安装的 libaio。

## 需要进一步确认的点
1. `pagure.io` 返回 HTML 的具体原因：是 anti-bot 验证页面、登录重定向，还是该归档版本确实已下架。可通过在非 CI 环境（浏览器）访问该 URL 验证。
2. 其他依赖（如 benchmark、zlib、zstd、fmt、boost、gflags、glog、googletest）的下载源（如 GitHub）未出现同类问题，是否只有 pagure.io 对 CI 环境有此类阻断。
3. 确认 libaio-libaio-0.3.113.tar.gz（PR 中作为二进制文件提交的本地备份）本身是否为合法有效的 tar.gz 归档，能否在 docker build 上下文中被正确 COPY 到镜像内。

# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 子项目缓存文件无效
- 新模式症状关键词: not a compressed or uncompressed tar file, wayland-protocols, packagecache, meson, subproject

## 根因分析

### 直接错误
```
#13 5.370 Dependency wayland-protocols for host machine found: NO. Found 1.33 but need: '>= 1.41'
#13 5.370 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#13 5.370 Looking for a fallback subproject for the dependency wayland-protocols
#13 5.370 Using wayland-protocols source from cache.
#13 5.370 ERROR: Subproject wayland-protocols is buildable: NO
#13 5.370 meson.build:2013:21: ERROR: failed to unpack archive with error: /opt/mesa-25.3.4/subprojects/packagecache/wayland-protocols-1.41.tar.xz is not a compressed or uncompressed tar file
```

### 根因定位
- 失败位置: Dockerfile:33 (meson setup build 步骤)，具体在 `meson.build:2013:21` 行（上游 mesa 源码）
- 失败原因: CI 预处理步骤从 GitLab 下载的 `wayland-protocols-1.41.tar.xz` 文件无效（非有效压缩 tar 包），Meson 作为 fallback 子项目解包时报错。系统已安装的 wayland-protocols 版本为 1.33，不满足 mesa 25.3.4 要求的 `>= 1.41`。

### 关键上下文
CI 日志中出现了一个 **不在 PR diff 范围内的额外构建步骤**（#12 [7/8]）：
```
#12 [7/8] RUN wget -q -O /tmp/wayland-protocols-1.41.tar.xz \
    https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz \
    && WP_HASH=$(sha256sum /tmp/wayland-protocols-1.41.tar.xz | cut -d' ' -f1) \
    && sed -i "s/^source_hash = .*/source_hash = ${WP_HASH}/" subprojects/wayland-protocols.wrap \
    && mkdir -p subprojects/packagecache \
    && mv /tmp/wayland-protocols-1.41.tar.xz subprojects/packagecache/wayland-protocols-1.41.tar.xz
#12 DONE 0.7s
```

该步骤下载耗时仅 0.7s（对一个 tar.xz 归档而言过快），且使用 `wget -q` 静默模式。虽 RUN 步本身以 exit code 0 完成，但下载的实际文件可能为 HTML 错误页或非 tar.xz 格式内容。

### 与 PR 变更的关联
PR 新增了一个全新 Dockerfile（`Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`），该 Dockerfile 本身不包含 wayland-protocols 的下载步骤。错误发生在 CI 流水线为构建 mesa 注入的预处理步骤中，具体有两层问题：

1. **直接层级**：GitLab release 下载 URL 返回的不是有效的 tar.xz 文件（可能是 HTML 重定向/错误页），导致文件缓存无效。
2. **间接层级**：系统预装的 wayland-protocols 版本过旧（1.33），无法满足 mesa 25.3.4 的构建要求（>= 1.41），迫使 Meson 回退到包缓存中的无效文件。

**此错误与 PR 的代码变更内容（Dockerfile 编写逻辑）无直接关联** — PR 新增的 Dockerfile 结构正确，问题出在 CI 平台为弥补系统 wayland-protocols 版本不足而注入的下载步骤上。

## 修复方向

### 方向 1（置信度: 中）
**修正 CI 注入步骤中的 GitLab 下载 URL**。GitLab 标准发布归档下载地址格式通常为：
`https://gitlab.freedesktop.org/wayland/wayland-protocols/-/archive/1.41/wayland-protocols-1.41.tar.xz`
而非 `/releases/1.41/downloads/` 路径。CI 预处理步骤中使用的 URL 可能不正确，导致下载内容非有效 tar.xz 文件。需要在 CI 模板中将下载源 URL 修正为 GitLab 官方归档路径。

### 方向 2（置信度: 中）
**在 Dockerfile 中通过 dnf 安装更新版本的 wayland-protocols**。当前 PR 的 dnf install 列表中仅包含 `wayland-devel`，不包含 `wayland-protocols-devel`。openEuler 24.03-LTS-SP4 可能提供更高版本的 wayland-protocols RPM 包，如果可用（>= 1.41），可以直接在 dnf install 阶段添加该包，避免 Meson 回退到子项目下载。

### 方向 3（置信度: 低）
**下载文件格式不匹配**。上游 wayland-protocols 发布的可能是 `.tar.gz` 而非 `.tar.xz`，下载的文件名与实际压缩格式不符也会导致解包失败。需要验证 GitLab 发布的实际文件格式。

## 需要进一步确认的点

1. CI 预处理步骤（下载 wayland-protocols 1.41）是在哪个 CI 脚本/模板中注入的？该步骤不在 PR diff 的 Dockerfile 中，需要确认注入来源以确定修改位置。
2. openEuler 24.03-LTS-SP4 的仓库中是否有 `wayland-protocols-devel >= 1.41` 的 RPM 包？如果有，可以直接通过 dnf 安装，无需额外下载。
3. GitLab `gitlab.freedesktop.org/wayland/wayland-protocols` 的 1.41 版本实际发布的归档文件格式是什么（`.tar.xz` 还是 `.tar.gz` 还是 `.tar.bz2`）？需要与 URL 后缀匹配。
4. 实际下载到的文件内容是什么（用 `file` 命令检测）？是否为 HTML 文本（错误页/登录页）而非 tar 归档？使用 `wget -q` 静默模式掩盖了下载错误。
5. 对比同路径下的 `25.3.4/24.03-lts-sp3/Dockerfile`，该 SP3 版本的 CI 构建是否也有类似的预处理步骤，以及是否成功。

## 修复验证要求

1. **code-fixer 必须先在 openEuler 24.03-LTS-SP4 容器中执行 `dnf list wayland-protocols-devel --showduplicates`**，确认是否有 >= 1.41 版本的 RPM 包。如有，方案 2 最简洁。
2. **code-fixer 必须用 `curl -I` 或浏览器实际访问 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz`**，确认该 URL 是否返回 200 且 Content-Type 为 `application/x-xz` 或 `application/octet-stream`（而非 `text/html`）。
3. 若 URL 不正确，code-fixer 需验证正确的 GitLab 归档下载 URL 格式，并在 CI 注入模板中修正，然后触发重建验证 `meson setup` 能正常解包 wayland-protocols 子项目。

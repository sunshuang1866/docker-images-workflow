# 修复摘要

## 修复的问题
Oozie 5.2.1 Maven 构建因 `releases.java.net` 仓库 SSL 证书过期导致 `org.glassfish.jaxb:txw2:2.4.0-b180608.0325` 依赖解析失败。

## 修改的文件
- `Bigdata/oozie/5.2.1/24.03-lts-sp3/Dockerfile`: 新增 txw2 依赖预安装步骤（将 Maven Central 的 `txw2:2.3.1` 以版本 `2.4.0-b180608.0325` 安装至本地仓库），并创建 Maven settings.xml 将 `releases.java.net` 仓库镜像到 Maven Central，阻止 Maven 访问已过期的 java.net 服务器。

## 修复逻辑

**根因**：Oozie 5.2.1 的 `fluent-job-api` 模块使用 `jax-maven-plugin:0.1.6` 进行 XJC 代码生成，其传递依赖链 `jax-maven-plugin -> jax-maven-plugin-core -> jaxws-tools -> jaxws-rt -> policy -> txw2:2.4.0-b180608.0325` 中，`txw2:2.4.0-b180608.0325` 为 GlassFish 预发布构建版本，仅托管于 `releases.java.net`（即 `maven.java.net`）。该服务器的 SSL 证书已于 2026-04-01 过期，HTTP 请求被 301 重定向至 HTTPS 后 PKIX 验证失败，HTTPS 后端返回 502 Bad Gateway。上游仓库 `https://github.com/apache/oozie` 的 `release-5.2.1` 分支根 pom.xml 中未声明 `releases.java.net` 仓库（该仓库来自传递依赖 POM），无法在源码层面排除。

**修复策略**：
1. **预安装 artifact**：从 Maven Central 下载 `txw2:2.3.1` JAR，通过 `mvn install:install-file` 以 `2.4.0-b180608.0325` 版本号安装至本地 Maven 仓库。`txw2:2.3.1` 与 `2.4.0-b180608.0325` 为同期构建（后者为 2018-06-08 预发布版本，前者为最后发布版本），API 兼容，且 txw2 无额外传递依赖。Maven 解析依赖时本地仓库优先，不会访问远程 `releases.java.net`。
2. **阻断过期仓库**：创建 `/root/.m2/settings.xml`，配置 `<mirror>` 将 `releases.java.net` 镜像至 Maven Central，确保其他可能引用该仓库的传递依赖也不会触发 PKIX 验证失败（即使 artifact 在 Central 上不存在也只会报清晰错误，而非 SSL 错误）。

**验证**：已从上游 `release-5.2.1` 获取 `pom.xml` 验证 `releases.java.net` 未在根 POM 中声明；确认 `txw2:2.3.1` 在 Maven Central 存在且无传递依赖；确认 `http://maven.java.net` 返回 301 重定向至 HTTPS，HTTPS 证书过期返回 502。

## 潜在风险
- `txw2:2.3.1` 替代 `2.4.0-b180608.0325` 用于 XJC 代码生成，若 JAXB 代码生成行为在两版本间有不兼容变更，可能导致生成的 Java 源码与预期不符。但两者为同期版本（2.3.1 发布版 vs 2018-06-08 预发布版），风险极低。
- 若 `releases.java.net` 仓库中还有其他 artifact 被引用且在 Maven Central 不存在，构建将因 "artifact not found" 失败（而非 SSL 错误），需进一步处理。
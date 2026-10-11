# 1024test 部署考核学生操作指南

本指南帮助你完成部署，具体验收以 `test_部署验收清单.md` 为准。纠错最多 10 次，命令和报错请自行记录。

## 1. Windows 获取、打包、上传

在 Windows 上打开 PowerShell，先确认 Git 已安装。使用 Git 从教师提供的仓库地址克隆项目，进入项目目录后检查当前状态、最近一次提交和目录内容，确认源码完整。不要在网页上下载压缩包。

检查完成后返回项目的上一级目录，使用 PowerShell 的压缩功能把项目内容打包成 `1024test.zip`。压缩包内应直接是项目文件，不应再套一层同名目录。

先通过 SSH 登录一次 Ubuntu，确认用户名、IP 地址和密码都正确；退出后，再使用 SCP 将 zip 文件上传到 Ubuntu 用户的家目录。上传完成后重新通过 SSH 登录 Ubuntu，后续操作全部在 SSH 终端完成。
## 2. Ubuntu 准备目录和软件

在 Ubuntu 中安装项目需要的解压工具、编辑器、Git、MySQL、Python、虚拟环境组件和 pip。然后在 `/home` 下创建名为 `test` 的目录，并让当前 Ubuntu 用户拥有该目录的操作权限。

把刚才上传的 zip 解压到 `/home/test`。解压后检查目录结构：`requirements.txt`、`schema.sql`、`src` 和 `deployment` 应该直接位于 `/home/test` 中，不能出现 `/home/test/1024test` 这样的多余二级目录。

将 `.env.example` 复制为 `.env`，限制 `.env` 的权限，并使用 vim 打开它。填写数据库密码，确认数据库地址、端口、库名、用户名和服务端口与实际配置一致。vim 保存时按 Esc，输入 `:wq` 后回车。
## 3. MySQL 建库建表和手动授权

使用 MySQL root 账户进入 MySQL，在 MySQL 提示符中执行项目提供的 `schema.sql`。该文件只负责创建 `1024test` 数据库、创建项目需要的表，并写入初始配置记录。

接下来必须由你自己完成 MySQL 应用账户的配置：创建名为 `test` 的 MySQL 用户，设置你自己决定的密码，并且只授予该用户对 `1024test` 数据库进行查询、插入、修改和删除的权限。不要授予全局权限、建表权限、删库权限或给其他用户授权的权限。

完成后使用 MySQL 的权限查看功能检查授权结果，确认实际权限符合最小权限要求。把刚才设置的密码填写到 `/home/test/.env` 的 `DB_PASSWORD` 中。项目不会提供创建用户和授权的 SQL。
## 4. 虚拟环境和依赖

在 `/home/test` 中创建 Python 虚拟环境，并激活它。使用项目的 `requirements.txt` 安装依赖，确认项目命令已经安装到该虚拟环境中。安装过程如果失败，应记录报错，检查 Python、pip、网络和虚拟环境状态，再计入一次纠错。

安装完成后退出虚拟环境。之后配置 systemd 时要使用该虚拟环境中的服务启动程序，不能误用系统 Python。

如果需要从任意目录执行客户端，应保持虚拟环境处于激活状态，或按教师要求创建 PATH 中的启动包装器；否则系统可能提示找不到 `1024test` 命令。
## 5. 前台验证和 systemd

先前台启动服务确认配置可用：

```bash
cd /home/test
source .venv/bin/activate
1024test-server
```

另开 SSH 窗口执行 `1024test -v`，确认服务可访问；然后回到服务窗口按 `Ctrl+C`。

安装 systemd unit：

```bash
sudo cp /home/test/deployment/1024test.service /etc/systemd/system/1024test.service
sudo vim /etc/systemd/system/1024test.service
sudo systemctl daemon-reload
sudo systemctl enable 1024test.service
sudo systemctl start 1024test.service
systemctl is-enabled 1024test.service
systemctl is-active 1024test.service
sudo systemctl status 1024test.service --no-pager
```

vim 中必须把 `User=REPLACE_WITH_UBUNTU_USERNAME` 替换为实际普通用户，并保持 `/home/test` 和 `/home/test/.venv/bin/1024test-server` 路径正确。启动失败时查看：

```bash
sudo journalctl -u 1024test.service -n 50 --no-pager
```

## 6. 重启和功能验收

先重启 Ubuntu 虚拟机。重新通过 SSH 登录后，检查 systemd 服务是否已经自动启动。

执行创建用户的功能，使用用户名 `user` 和密码 `123456`。标准输出应为 `true`。随后执行登录功能，看到 `password：` 提示后输入 `123456`，应看到 `logining`。

使用 MySQL root 删除刚才创建的 `user` 账户。删除后重启 1024test 服务，再次执行登录功能，应提示 `无该用户`。

停止 1024test 服务，再执行版本检查功能。此时应看到“无法执行”提示，并且程序退出码必须是非零值。验收结束后重新启动服务。
## 7. 推送自己的仓库

在 Ubuntu 的项目目录中初始化 Git 仓库，查看当前工作区状态，并确认 `.env` 和 `.venv` 已被忽略。然后把项目文件加入提交，填写清晰的提交说明，设置主分支名称，添加自己的 GitHub 或 Gitee 仓库地址，最后推送到远程仓库。

推送前必须再次检查提交内容，确保没有包含 `.env`、`.venv`、zip 压缩包、数据库转储文件或任何密码。systemd 配置文件中的 `REPLACE_WITH_UBUNTU_USERNAME` 也必须已经替换成真实的 Ubuntu 用户名。
## 8. 交付证据

- Git clone、压缩、scp 命令记录
- `/home/test` 目录结构
- `SHOW GRANTS` 输出
- systemd `enabled` 和 `active` 输出
- 重启后创建、登录、删除、停服务的结果
- 纠错次数（不超过 10 次）
- GitHub/Gitee 仓库地址和内容展示



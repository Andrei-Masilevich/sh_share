# ShELLShare

It's HTTP service that deploys encrypted data as an Web-object.
The original purpose was to be used for sharing personal data for ShELL tools. But it could be used for different ways.

This service uses ZIP archive as a source of data that is considered as separate object. It uses synonyms to get files inside the object.
It is possible to add other types (ex. 7-ZIP) that supports meta information to browse archive.

Object could be downloaded by date or to get latest one by _latest_ keyword. 

Synonyms are used to get files inside object. For instance ShELL-tools exports ZIP archive with two files inside, that have **.tar.gz** and **.key** extensions. 
Let's suppose it was configured following synonyms: _key_ for **.key** and
_data_ for **.tar.gz**

Key file from the latest object could be retrieved by path: 

```bash
[service url]/latest/key
```

The rest one by:

```bash
[service url]/latest/data
```

Without synonyms files are accessible by file name inside archive. Ex.:

```bash
[service url]/latest/export.2023-01-05_18-57.tar.gz
```
or
```bash
[service url]/arch.2023-01-05_18-57/export.2023-01-05_18-57.tar.gz
```
if it was from arch.2023-01-05_18-57.zip

Current version supports only the single group of objects (diferented by date only) 


# Security

The main idea is making this project as simple and as cheap as possible without significant leaks of security.
For that purpose it's supposed to use encrypted data for sharing and unpredictable HTTP path.
But **HTTPS support, HTTP authentication and routing** are implemented by external tools ([Nginx](https://www.nginx.com/) or [Squid](http://www.squid-cache.org/Intro/))

Unpredictable HTTP path means that service is not accesable by any standart path like '/' but **genarate random readable name** for a path. Ex. to download the latest version of an object (as a ZIP file):

```bash
[domain url]/blabladoom/latest
```
for previos example:

```bash
[domain url]/blabladoom/latest/key
```
Service should be restarted to get new one freak but memorizable name.

```bash
[domain url]/razzmazz/latest/key
```

# Usage with Telegram

For security reasons, the service must restart often enough to clear the next secret path (Ansible setups it with cron). It is not convenient to attend remote service every time to get new secret URL.
Secret URL retriving was impelemented here via Telegram private [channel](https://telegram.org/tour/channels#:~:text=Channels%20are%20a%20tool%20for,have%20the%20right%20to%20post.). To use this technike you should:
1. Create private channel
2. Create bot (via @BotFather)
3. Add new bot as Administator of this channel limited Post Message rights only
4. Finally You as having rights to Post Message to this channel should public special command to get actual secret URL from bot.

Ex. If you configured _get_secret_ as the command. Type _/get_secret_ to get URL. Look at *Deploy* section to get information about configuration stuff. 

# Deploy

This project is secure enough while been binding with HTTPS provided by [Nginx](https://www.nginx.com/) (for instance).

There two way to deploy project with Nginx (for Squid it is pretty same):

## Remotely with Ansible:
---
```bash
ansible-playbook --ask-become-pass ./deploy/ansible/deploy_with_nginx.yaml
```

or by connecting to root session (default for some cloud providers):

```bash
ansible-playbook ./deploy/ansible/deploy_with_nginx.yaml
```

> Variables are required inside _./deploy/ansible/group_vars_:

```bash
cd ./deploy/ansible/group_vars
cp all.yaml.sample all.yaml 
```
Mandatory variables:

|*name*|*description*|
|--|--|
|sh_share_deploy_local_share_dir|Local folder with initial list of archive files to share|
|sh_share_deploy_external_inet_interface|Remote interface name that route to the Internet (ex. enp0s3, eth0, eth2)|
|sh_share_deploy_external_ipv4|IP (v4) address that is routed to the Internet|
|sh_share_deploy_domain|Domain name corresponds to certificate used to access the service|
|sh_share_deploy_certificate_file|Secret certificate file for HTTPS in format CERTIFICATE+PRIVATE KEY|
|**notifications**||
|sh_share_deploy_telegram_accept_command|Command used to request service URL from private channel (ex. get_my_secret_url)|
|sh_share_deploy_telegram_bot_token|Telegram Bot token that was delivered by @BotFather|
|sh_share_deploy_telegram_channel_id|Private channel numeric ID. There are some [hints](https://telegram-bot-sdk.readme.io/reference/getupdates) to get it|
|sh_share_deploy_telegram_off|Do not use Telegram notifier|

**This way is preferable because it does not only deploy service for special system user sh_share, but setup crono reloading task and firewall settings**

## Locally at the host machine:
---

This way is the low level used by Ansible for one of it's steps.

1. Create .env file with custom settings. Variables:

|||
|--|--|
|SH_SHARE_SERVICE_DOMAIN|Look at. *sh_share_deploy_domain*|
|SH_SHARE_SERVICE_CERTIFICATE|Look at. *sh_share_deploy_certificate_file*|
|SH_SHARE_SERVICE_DIR|Folder with the files to share|
|SH_SHARE_SERVICE_TELEGRAM_ACCEPT_COMMAND|Look at. *sh_share_deploy_telegram_accept_command*|
|SH_SHARE_SERVICE_TELEGRAM_BOT_TOKEN|Look at. *sh_share_deploy_telegram_bot_token*|
|SH_SHARE_SERVICE_TELEGRAM_CHANNEL_ID|Look at. *sh_share_deploy_telegram_channel_id*|
|SH_SHARE_SERVICE_TELEGRAM_OFF|Look at. *sh_share_deploy_telegram_off*|

> There is no network setting here because it doesn't setup firewall.

2. Run:

```bash
bash ./deploy nginx
```




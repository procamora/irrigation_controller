# irrigation_controller
Project to create an irrigation controller bot



CREAR KEY SSH

eval "$(ssh-agent -s)"

mkdir -p /root/.ssh
chmod 700 /root/.ssh

touch /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys  # le quitamos los permisos necesarios

# modificcar inventory con la ip de la rp

cd ansible
ansible-playbook -i inventory main.yml -v

```
"""commands
Name:
procamora irrigation controller

Username:
procamora_irrigation_bot

Description:
This is a bot to manage network scanner using nmap. A local agent is required to perform the scans

About:
This bot has been developed by @procamora

Botpic:
<imagen del bot>

Commands:
scan - scan networks
online - get hosts online
offline - get hosts offline
pdf - get pdf report
help - Show help
start - Start the bot
"""
```

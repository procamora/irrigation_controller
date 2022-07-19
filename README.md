# irrigation_controller
Project to create an irrigation controller bot


preparar ssh para conexion con ansible

```bash
sudo mkdir -p /root/.ssh
sudo chmod 700 /root/.ssh

sudo touch /root/.ssh/authorized_keys
sudo chmod 600 /root/.ssh/authorized_keys  # le quitamos los permisos necesarios
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQDXEcpTAqxQemrkIpEX45ylTLsPhDgko6Qugfv6B1/cioLaeXtI03NgKKMcWv4yMmKMLvJg4adxkEjpn/5IKEA13ljCMZ+Ue29Su+oOYSU8bo3bLlm+h5hvVJeso0irdnrqILNgL4yw38ebmC8IZaKBhiwiGD8sT/LD9VZSqaxnbQ== key used for automation service connections" | sudo tee /root/.ssh/authorized_keys
```


# modificcar inventory con la ip de la rp

```bash
cd ansible
ansible-playbook -i inventory main.yml -v
```



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

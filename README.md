# irrigation_controller
Project to create an irrigation controller bot


# BORRAR PROJECTO Y DIOCUMENTAR LA CREACION PASO A PASO EN GOOGLE CLOUD
 - modificar ssh de pi para acceso por certi unicamente
 - acceso para usuario procamora solo
 - disable user pi
 - verificar que procamora accede bien por certi antes de permitir solo por certi
 - verificar escalada a root de procamora con su pass
 - CREACION PROJECTO
 - HJABITLITAR API GOOGLE CALENDAR
 - CREAR API GOOGLE CALENDAR
 - EJECUTAR APLICACION Y PRROBAR
 - PASAR A PRODUCCION PARA QUE EL TOKEN NO DURE 7 DIAS

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
sudo apt install ansible
ansible-galaxy collection install community.general
ansible-playbook -i inventory main.yml -v
```


# ERROR: Failed building wheel for bcrypt (error: Rust 1.48.0 does not match extension requirement >=1.56.0)

si falla al ejecutar pip3 install -r requirements.txt

```bash
# https://www.how2shout.com/linux/how-to-install-and-use-rust-on-debian-11-bullseye/
 rustc --version # => rustc 1.48.0 (471d696c7 2020-12-10)

curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
rustc --version # =>  rustc 1.65.0 (897e37553 2022-11-02)
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



![diagram][diagram]


[diagram]: diagram.drawio.svg



## API GOOGLE CALENDAR

https://console.cloud.google.com/apis/credentials?project=procamora-irrigation&cloudshell=true&orgonly=true&supportedpurview=project

gcloud projects create procamora-irrigation --name="Irrigation Controller"
gcloud services enable calendar-json.googleapis.com --project=procamora-irrigation
gui -> APIs & Services > OAuth consent screen.
gio -> APIs & Services > Credentials -> ID de clientes OAuth 2.0 


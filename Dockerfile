#FROM registry.redhat.io/rhel8
FROM docker.io/library/fedora:37
LABEL Maintainer="Pablo Rocamora <pablojoserocamora@gmail.com>"
LABEL Description="Fedora Irrigation"
LABEL Version="1.0"
LABEL License=GPLv2

# docker builder prune
# docker system prune -a


# mlocate
RUN dnf update -y \
  && dnf install -y vim sudo curl wget util-linux-user iproute initscripts python3 git dnf-plugins-core iputils \
    net-tools unzip langpacks-en bind-utils tree jq nc python3 python3-devel python3-pip crontabs \
  && dnf clean all


# Set the locale
#RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
#    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8
#localedef -i en_US -f UTF-8 en_US.UTF-8
RUN sed -i 's/^LANG=.*/LANG="en_US.utf8"/' /etc/locale.conf


#RUN echo 'root:toor' | chpasswd

#RUN echo "*/1  *  *  *  * procamora    python3 /data/watchdog.py" | tee -a /etc/crontab

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

RUN useradd -s /bin/bash --no-log-init -m -U -u 1000 --home /data procamora \
    && chown -R procamora /data \
    && echo 'procamora ALL=(ALL) NOPASSWD: /usr/bin/tee, /usr/sbin/crond' | tee -a /etc/sudoers.d/procamora
USER procamora
WORKDIR /data
#RUN chmod 755 /data

COPY *.py ./
COPY cron.j2 ./
RUN ls ./*


EXPOSE 22
#ENV TG_ADMIN=1123123
#ENV TG_BOT_TOKEN=sdfsdfsdfsdfsdfsdfsdf
#ENV TG_BOT_DEBUG_TOKEN=sdfsdfsdfsdfsdfsdfsdf

COPY ./entrypoint.sh /data
ENTRYPOINT ["./entrypoint.sh"]


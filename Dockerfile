#FROM registry.redhat.io/rhel8
FROM docker.io/library/fedora:37
LABEL Maintainer="Pablo Rocamora <pablojoserocamora@gmail.com>"
LABEL Description="Fedora Irrigation"
LABEL Version="1.0"
LABEL License=GPLv2

# docker builder prune
# docker system prune -a


USER root
WORKDIR /root
RUN chmod 755 /root

# mlocate
RUN dnf update -y \
  && dnf install -y vim sudo curl wget util-linux-user iproute initscripts python3 git dnf-plugins-core iputils \
    net-tools unzip bind-utils tree jq nc python3 python3-devel python3-pip \
  && dnf clean all

# Set the locale
#RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
#    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8
#localedef -i en_US -f UTF-8 en_US.UTF-8
RUN sed -i 's/^LANG=.*/LANG="en_US.utf8"/' /etc/locale.conf


RUN echo 'root:toor' | chpasswd
#RUN chsh -s $(command -v zsh) root


COPY requirements.txt ./
RUN pip3 install -r ./requirements.txt
COPY *.py ./
COPY cron.j2 ./
RUN ls ./*


EXPOSE 22
#ENV TG_ADMIN=1123123
#ENV TG_BOT_TOKEN=sdfsdfsdfsdfsdfsdfsdf
#ENV TG_BOT_DEBUG_TOKEN=sdfsdfsdfsdfsdfsdfsdf

COPY ./entrypoint.sh /root
ENTRYPOINT ["./entrypoint.sh"]


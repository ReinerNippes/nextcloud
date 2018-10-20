#!/bin/bash
#
# Prepare system for nextcloud devel
#
prepare_ubuntu() {
        $SUDO apt install software-properties-common -y
        $SUDO apt-add-repository ppa:ansible/ansible -y
        $SUDO apt update -y
        $SUDO apt install ansible python-mysqldb python-netaddr mc vim git facter -y
        echo
        echo "Ubuntu Sytem ready for nextcloud."
        echo
}

prepare_debian() {
        $SUDO apt install dirmngr mc vim git facter -y
        $SUDO apt update -y
        $SUDO apt install python-mysqldb python-pip python3-pip facter -y
        $SUDO pip install pip -U
        $SUDO pip install setuptools -U
        $SUDO pip install ansible -U
        echo
        echo "Debian Sytem ready for nextcloud."
        echo
}

prepare_raspbian() {
        $SUDO apt install dirmngr mc vim git libffi-dev facter -y
        $SUDO apt dist-upgrade -y
        $SUDO apt install python-mysqldb python-pip python3-pip facter -y
        $SUDO pip install pip -U
        $SUDO pip install setuptools -U
        $SUDO pip install ansible -U
        echo
        echo "Rasbpian System ready for nextcloud."
        echo
}

prepare_centos() {
        $SUDO yum install epel-release -y
        $SUDO yum install ansible git vim mc python-mysqldb python-netaddr facter -y
        $SUDO yum update -y
        echo
        echo "CentOS Sytem ready for nextcloud."
        echo
}

usage() {
        echo
        echo "Linux distribution not detected."
        echo "Use: IB=[Ubuntu|Debian|CentOS|raspbian] setup_ec2.sh"
        echo "Other distributions not yet supported."
        echo
}

# get infos about linux distro
if [  -f /etc/os-release ]; then
        . /etc/os-release
elif [ -f /etc/debian_version ]; then
        $ID=debian
fi

# root or not
if [[ $EUID -ne 0 ]]; then
  $SUDO=sudo
else
  $SUDO=''
fi


case $ID in
        'ubuntu')
                prepare_ubuntu
        ;;
        'debian')
                prepare_debian
        ;;
        'raspbian')
                prepare_raspbian
        ;;
        'centos')
                prepare_centos
        ;;
        *)
                usage
        ;;
esac

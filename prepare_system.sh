#!/bin/bash -uxe
#
# Prepare system for nextcloud installtion
#

prepare_ubuntu() {
        $SUDO apt update -y
        $SUDO apt-get -o Dpkg::Options::="--force-confold" -fuy dist-upgrade
        $SUDO apt-get -o Dpkg::Options::="--force-confold" -fuy install software-properties-common curl git mc vim facter python3 python3-setuptools python3-apt python3-pip python3-passlib python3-wheel python3-bcrypt aptitude -y
        $SUDO [ $(uname -m) == "aarch64" ] && $SUDO apt install gcc python3-dev libffi-dev libssl-dev make -y
        $SUDO pip3 install ansible -U

        set +x
        echo
        echo "------------------------------------------------------"
        echo
        echo "   Ubuntu System ready to install nextcloud."
        echo
        ansible --version
        echo
        echo "------------------------------------------------------"
        echo
}

prepare_debian() {
        $SUDO apt update -y
        $SUDO apt-get -o Dpkg::Options::="--force-confold" -fuy dist-upgrade
        $SUDO apt-get -o Dpkg::Options::="--force-confnew" -fuy install dirmngr curl git mc vim facter python3 python3-pip python3-apt python3-passlib python3-bcrypt python3-wheel python3-setuptools aptitude -y
        [ $(uname -m) == "aarch64" ] && $SUDO apt install gcc python3-dev libffi-dev libssl-dev make -y
        $SUDO pip3 install ansible -U

        set +x
        echo
        echo "------------------------------------------------------"
        echo
        echo "   Debian System ready to install nextcloud."
        echo
        ansible --version
        echo
        echo "------------------------------------------------------"
        echo
}

prepare_raspbian() {
        $SUDO apt update -y
        $SUDO apt-get -o Dpkg::Options::="--force-confold" -fuy dist-upgrade
        $SUDO apt install dirmngr mc vim git libffi-dev curl facter python python-apt python-pip python-passlib python-bcrypt aptitude ansible -y
        $SUDO pip install ansible -U

        set +x
        echo
        echo "------------------------------------------------------"
        echo
        echo "   Rasbpian System ready to install nextcloud."
        echo
        ansible --version
        echo
        echo "------------------------------------------------------"
        echo
}

prepare_centos() {
        $SUDO yum install epel-release -y
        $SUDO yum install git vim mc curl facter python36 python36-pip ansible -y
        $SUDO yum update -y
        $SUDO pip3 install ansible -U

        set +x
        echo
        echo "------------------------------------------------------"
        echo
        echo "   CentOS System ready to install nextcloud."
        echo
        ansible --version
        echo
        echo "------------------------------------------------------"
        echo
}

prepare_fedora() {
        $SUDO dnf install git vim mc curl facter python3 python3-dnf python3-pip python3-libselinux python3-bcrypt python3-passlib ansible -y
        $SUDO dnf update -y

        set +x
        echo
        echo "------------------------------------------------------"
        echo
        echo "   Fedora System ready to install nextcloud."
        echo
        ansible --version
        echo
        echo "------------------------------------------------------"
        echo
}

prepare_amzn() {
        $SUDO amazon-linux-extras install epel -y
        $SUDO amazon-linux-extras install python3 -y
        $SUDO yum install git vim mc curl facter -y
        $SUDO yum update -y
        $SUDO pip3 install ansible -U
        $SUDO pip3 install passlib -U
        $SUDO pip3 install bcrypt -U

        set +x
        echo
        echo "------------------------------------------------------"
        echo
        echo "   Amazon Linux 2 ready to install nextcloud."
        echo
        ansible --version
        echo
        echo "------------------------------------------------------"
        echo
}

usage() {
        echo
        echo "Linux distribution not detected."
        echo "Use: ID=[ubuntu|debian|centos|raspbian|amzn|fedora] prepare_system.sh"
        echo "Other distributions not yet supported."
        echo
}

if [  -f /etc/os-release ]; then
        . /etc/os-release
elif [ -f /etc/debian_version ]; then
        $ID=debian
fi

# root or not
if [[ $EUID -ne 0 ]]; then
  SUDO='sudo -H'
else
  SUDO=''
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
        'fedora')
                prepare_fedora
        ;;
        'amzn')
                prepare_amzn
        ;;

        *)
                usage
        ;;
esac


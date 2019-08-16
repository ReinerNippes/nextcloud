#!/bin/bash -uxe
#
# Prepare system for nextcloud devel
#

install_pip () {
	curl https://bootstrap.pypa.io/get-pip.py | $SUDO $PYTHON_BIN
	$SUDO $PIP_BIN install setuptools -U
	$SUDO $PIP_BIN install ansible -U
	$SUDO $PIP_BIN install netaddr -U
	$SUDO $PIP_BIN install dnspython -U
	$SUDO $PIP_BIN install passlib -U
	$SUDO $PIP_BIN install bcrypt -U
}

prepare_ubuntu() { 
	$SUDO apt update -y
	$SUDO apt dist-upgrade -y
	$SUDO apt install software-properties-common curl git mc vim facter python3 python3-distutils python3-requests -y
	$SUDO [ $(uname -m) == "aarch64" ] && apt install gcc python3-dev libffi-dev libssl-dev make -y

	PYTHON_BIN=/usr/bin/python3
	PIP_BIN=/usr/local/bin/pip
	install_pip
		
	echo
	echo "Ubuntu Sytem ready for nextcloud." 
	echo
}

prepare_debian() { 
	$SUDO apt update -y
	$SUDO apt dist-upgrade -y
	$SUDO apt install dirmngr curl git mc vim facter python3 python3-distutils python3-requests aptitude -y
	$SUDO [ $(uname -m) == "aarch64" ] && apt install gcc python3-dev libffi-dev libssl-dev make -y
	
	PYTHON_BIN=/usr/bin/python3
	PIP_BIN=/usr/local/bin/pip
	install_pip
	
	echo
	echo "Debian Sytem ready for nextcloud."
	echo
}

prepare_raspbian() {
	$SUDO apt update -y
	$SUDO apt dist-upgrade -y
	$SUDO apt install dirmngr mc vim git libffi-dev curl facter -y
	PYTHON_BIN=/usr/bin/python
	install_pip
	
	echo
	echo "Rasbpian System ready for nextcloud."
	echo
}

prepare_centos() { 
	$SUDO yum install epel-release -y
	$SUDO yum install git vim mc curl facter libselinux-python python36 python36-pip -y
	$SUDO yum update -y

	PYTHON_BIN=/usr/bin/python3.6
	PIP_BIN=/usr/local/bin/pip
	install_pip
	
	echo
	echo "CentOS Sytem ready for nextcloud."
	echo
}

usage() { 
	echo
	echo "Linux distribution not detected."
	echo "Use: ID=[Ubuntu|Debian|CentOS|raspbian] setup_ec2.sh"
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
	*)
		usage
	;;
esac

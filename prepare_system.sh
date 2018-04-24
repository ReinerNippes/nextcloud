#!/bin/bash
#
# Prepare system for nextcloud devel
#
prepare_ubuntu() { 
	sudo apt install software-properties-common -y
	sudo apt-add-repository ppa:ansible/ansible -y
	sudo apt update -y
	sudo apt install ansible python-mysqldb mc vim git -y
	echo
	echo "Ubuntu Sytem ready for nextcloud installation." 
	echo
}

prepare_debian() { 
	sudo apt install dirmngr mc vim git -y
	sudo apt update -y
	sudo apt install python-mysqldb python-pip python3-pip -y
	sudo pip install pip -U
	sudo pip install setuptools -U
	sudo pip install ansible -U
	echo
	echo "Debian Sytem ready for nextcloud installation."
	echo
}

prepare_centos() { 
	sudo yum install epel-release -y
	sudo yum install ansible git vim mc python-mysqldb -y
	sudo yum update -y
	echo
	echo "CentOS Sytem ready for nextcloud installation."
	echo
}

prepare_amazon() {
        sudo yum install epel-release -y
        sudo yum --enablerepo epel install ansible git vim mc  mysql-devel -y
        sudo yum --enablerepo epel update -y
        echo
        echo "Amazon Linux Sytem ready for nextcloud  installation."
        echo
}

usage() { 
	echo
	echo "Linux distribution $ID not detected."
	echo "Use: ID=[ubuntu|debian|centos|amzn] setup_ec2.sh"
	echo "Other distributions not yet supported."
	echo
}

if [  -f /etc/os-release ]; then 
	. /etc/os-release
elif [ -f /etc/debian_version ]; then
	$ID=debian
fi
	
case $ID in
	'ubuntu')
		prepare_ubuntu
	;;
	'debian')
		prepare_debian
	;;
	'centos')
		prepare_centos
	;;
        'amzn')
                prepare_amazon
        ;;
	*)
		usage
	;;
esac

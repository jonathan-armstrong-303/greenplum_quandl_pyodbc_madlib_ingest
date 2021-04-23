# Quandl data ingestion into Greenplum database with pyodbc and subsequent analysis with Apache MADlib ML library
## Synopsis

This project is a tutorial detailing ingestion of financial data (Quandl.com provides an exceptionally nice API with many datasets) into a Greenplum database with pyodbc that can be subsequently analyzed/manipulated with the Apache MADlib ML library.

## Motivation

There is often a dearth of "soup to nuts" tutorials and beginners are often left to the frustrating effort of (in this case) trying to piece together disparate pieces of a puzzle including database setup, ODBC configuration, Python code, and ancillary packages and installations.  

The purpose is to tie together an entire flow from ingesting a data source (from Quandl.com) into a Pandas dataframe, doing a couple of rudimentary manipulations on it, inserting it into the database, and showing how it can be subsequently manipulated with the Apache MADlib machine learning library.  I've included a lot of low-level detail on each step that will hopefully save someone quite a bit of time; the only downside is that a good chunk of the prerequisite installation steps aren't totally amenable to automation thanks to things like Pivotal requiring registration for a lot of the downloads.  

## Prerequisites (Hardware)

This project assumes that the user is running a Greenplum cluster per the author's previous installation (see https://github.com/jonathan-armstrong-303/vagrant_greenplum_6-1-4_install) in the Vagrant environment.  Greenplum's installation proved to be a bit... "opaque", but I was able to successfully create a nearly-100% automated build in the Vagrant environment, so the user shouldn't be intimidated by what would otherwise be the extremely esoteric installation process.

This installation could undoubtedly be easily tweaked to just run on a local Postgres instance {MORE HERE}

This was performed on my home Linux desktop (4 cores/4.2 GHz processors/64 GB memory) and allocated 12GB RAM to each of the four Greenplum nodes in Vagrant (admittedly 4GB less than the minimum recommended) running Ubuntu 20.04.

Configuration was tested with Vagrant 2.2.6.  (If Vagrant is not installed, I've provided up-to-date instructions on that below.)
# Installation (Overview)

Unfortunately, there are some annoyances (namely Pivotal requiring registration and consequent manual downloading of a lot of the necessary packages) that prevented this from easily being a completely automated installation script, but this isn't a huge show-stopper.

The user will need to register on both 
## Installation [pyodbc]

Note that there are five sections regarding installation prerequisites.  [The tl;dr]:

1. The Vagrant application itself [if not already installed]
2. External Vagrant packages;
3. Everything that must be done as root;

... one mandatory "postrequisite":

4. Everything that must be done as gpadmin;

... and one *optional* script: 

5.  reset /etc/ssh/sshd.config params to be more security conscious after passwordless ssh is established between all nodes (keep reading for details).

**The longer explanation:**

The reason for the aforementioned third "postrequisite" script was due to a couple of factors:

The author had an incredible amount of difficulty with a couple of [usually] fairly trivial tasks when setting up this Vagrant cluster:

1. Setting up passwordless ssh between nodes which necessitated changing some of the /etc/sshd/sshd.config parameters (I don't even know if these were _necessarily_ necessary to remove; however, after a couple of days of flailing with what should have been a trivial task, I did not change with the configuration once it was finally working);

2. Getting the final lap of the installation (which must be run as the "gpadmin" user -- not root) to transpire using a regular Vagrant provisioning script executed when the cluster is built.

(1) was finally resolved by installing the vagrant reboot plugin and rebooting the cluster after disabling the SELINUX security module, but there were continual problems getting (2) to transpire in a totally turnkey manner.

The only way I could get the gpadmin ("postrequisite") portion of the installation to work in a completely automated manner was found to be highly unintuitive and aesthetically lacking (namely, trying to run everything as "su gpadmin" or creating a crontab that fired off a one-time disposable installation script that would self-destruct after the first instantiation of the cluster).  In light of this, there is [one] semi-manual step of this installation process, which merely involves scping over a single script to the Greenplum master node and manually executing it as the gpadmin user.  

## Pre-Installation: Virtualbox/Vagrant Installation

If you already have Virtualbox and Vagrant installed (this build was tested with Vagrant 2.2.6) you can skip to the next installation step (if really unfamiliar with Vagrant, it would behoove you to do a little familiarization with it just so you're able to start/stop/reload/etc Vagrant boxes elegantly).

Update all packages and install Oracle Virtualbox:

    sudo apt update
    sudo apt install virtualbox

Visit Vagrant download page at https://www.vagrantup.com/downloads.html
(Could not get the apt update to work on my system -- hence the need to visit the download page itself.)

Download latest Vagrant version [2.2.14 as of time of writing], unzip, and install:

    cd ~/Downloads
    unzip ./vagrant_2.2.14_linux_amd64.zip
    sudo apt install vagrant

Check status of Vagrant install. I got "2.2.6" as output (even though I supposedly installed 2.2.14!)

    vagrant --version

Create a sample directory for Vagrant boxes

    mkdir -p ~/vagrant
    cd ~/vagrant

You will place the "Vagrantfile" Vagrant config in the ~/vagrant directory.
However, don't "vagrant up" yet.  We still need to install some Vagrant plugins

## Installation (Vagrant Plug-Ins/Grab Greenplum Binary For Posterity)

Install plugins which are necessary &/or helpful in the subsequent Greenplum install:

    vagrant plugin install vagrant-scp
    vagrant plugin install vagrant-hostsupdater
    vagrant plugin install vagrant-disksize
    vagrant plugin install vagrant_reboot_linux

You are now ready to initialize the Vagrant cluster:

    vagrant up
    
## OPTIONAL: download the Greenplum install binary for posterity

You don't _need_ to do this here as it's automated in the script install -- but I've
had occasional issues where the gpdb binary downloads painfully slowly so it's good to have it on
hand in case for posterity you need to do a quick rebuild and are having issues downloading 

    curl -L https://github.com/greenplum-db/gpdb/releases/download/6.14.0/open-source-greenplum-db-6.14.0-rhel7-x86_64.rpm -o open-source-greenplum-db-6.14.0-rhel7-x86_64.rpm

Copy Greenplum binary to guest:

    vagrant scp open-source-greenplum-db-6.14.0-rhel7-x86_64.rpm :open-source-greenplum-db-6.14.0-rhel7-x86_64.rpm

## gpadmin user installation (run this _after_ running "vagrant up").
## This is everything that must be installed as the gpadmin user.

Copy over the final "gpadmin" install script from this repository to the master node.

    scp setup_master_gpadmin_ssh.sh gpadmin@mdw:/home/gpadmin

Note: if you've done any rework, you might get the hyperbolic "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!" warning.  
To bypass this error, clean up the known hosts file appropriately.  
(On my little local Ubuntu setup here, this is facilitated by just "rm ~/.ssh/*"; this might be too draconian for your own environment though, so proceed with caution.  To execute the final "gpadmin section" of the Greenplum installation:

    vagrant ssh mdw
    sudo su gpadmin
    cd /home/gpadmin
    chmod +x ./setup_master_gpadmin_ssh.sh
    ./setup_master_gpadmin_ssh.sh
    
## OPTIONAL: Reset sshd parameters

You may wish to restore sshd parameters to be a bit more security conscious.  Needless to say, this configuration is anything but hardened for a security environment (found in the *reset_sshd_params.sh* script in this repository).  Run the following on each of the four nodes:

    sudo su -

    sed -ie 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -ie 's/ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
    sed -ie 's/UsePAM no/UsePAM yes/' /etc/ssh/sshd_config
    echo "UsePAM yes" >> /etc/ssh/sshd_config
    systemctl restart sshd.service
    egrep "^PasswordAuthentication|^ChallengeResponseAuthentication|^UsePAM" /etc/ssh/sshd_config


# Tests

You should see the following message upon completion of the install (the script restarts Greenplum one time after installation to effect changes made to the .bashrc file):

**20210317:19:34:56:008419 gpstop:mdw:gpadmin-[INFO]:-Restarting System...**

Create a test database and connect:

    createdb development
    psql development
    
"\q" exits from psql.

You are now ready to use Greenplum.  To start the database after halting/reloading the Vagrant cluster:

    gpstart

## Contributors

Dana Brenn's Vagrant install for Greenplum 4.3.4.0 was the initial inspiration for this project.

https://github.com/danabrenn/greenplum-4-3-4-0_full_install

## License



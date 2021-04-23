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

Before proceeding, the user needs to register at both the VMWare Tanzu website (for Greenplum binaries) as well as Quandl (for access to the Quandl API which is used to ingest the palladium/platnium price dataset in the example).  
 
https://login.run.pivotal.io/login
https://www.quandl.com/

There are two main sections to the installation section: installing the pyodbc package and ODBC files in order to connect to the Greenplum (or potentially Postgres) database from the host system, and installation of the Apache MADlib machine learning library (The MADlib install isn't necessary to get this code working and can be skipped if desired).

## Installation [pyodbc and Progress ODBC driver]

Before proceeding, ensure that instructions are issued on the appropriate server (i.e., host or guest [i.e., Greenplum master node]).  

**RUN ON HOST (i.e. local server)**

**INSTALLING THE DRIVER AND MODIFYING THE DSN**

Ensure you install the requisite unixodbc packages before the pip pyodbc install.
I was able to  install everything incorrectly, uninstall it, and reinstall with no problems
so there _shouldn't_ be any irritations with half-installed packages if you need to redo.

    sudo apt-get install -y unixodbc
    sudo apt-get install -y unixodbc-dev

You need to register before you can download from the Pivotal website; no curl install 
Once you've done this, the requisite tar file is underneath 
"Progress DataDirect Connect64 XE for ODBC for Pivotal Greenplum for Linux 64-bit"
https://network.pivotal.io/products/pivotal-gpdb#/releases/848083/file_groups/3302

Download the file from the website and extract: 
    cd ~/Downloads 
    tar -zxvf "PROGRESS_DATADIRECT_CONNECT64_ODBC_7.1.6+7.16.389.HOTFIX_LINUX_64.tar.gz"

run extracted Korn shell install script [in same directory you just executed the tar]
run dos2unix and also install Korn shell if necessary [it's missing on Ubuntu 20.04]

    sudo apt install dos2unix
    dos2unix unixmi.ksh
    sudo apt install ksh

Create the necessary installation directory and make it universal read/write:

    sudo mkdir -p /opt/Progress; sudo chmod 777 /opt/Progress

Run installation script for Progress ODBC connection -- usual "Y" / "YES" answers

    cd ~/Downloads
    ./unixmi.ksh

Mindlessly enter the usual Y/YES/etc registration/installation information when prompted 
(not included for brevity)
Enter the following for ++both++ key & serial number:
(please refer to https://gpdb.docs.pivotal.io/6-15/datadirect/datadirect_ODBC_71.html for potential updates)

    1076681984

Change to newly installed ODBC directory and source in ODBC parameters:

    cd /opt/Progress/DataDirect/Connect64_for_ODBC_71/
    source odbc.sh

Make a note of the requisite $ODBCINI (/opt/Progress/DataDirect/Connect64_for_ODBC_71/odbc.ini) parameters.
and then change to the following values listed in the $ODBCINI file.
Again, this is congruent on my previous Vagrant Greenplum install. YMMV may vary in your environment
"development" was the test database created earlier and is not a standard Postgres/Greenplum database.

    vi $ODBCINI
    
Modify the following parameters in the $ODBCINI file as follows:

    
    LogonID=gpadmin
    Password=gpadmin
    Database=development
    HostName=192.168.0.200
    PortNumber=5432
    
Validate that the changes were successfully affected:

    egrep -i "database|hostname|portnumber|logonid|password" $ODBCINI|egrep -vi "keypassword|keystorepassword" 

Verify the driver version.

    cd /opt/Progress/DataDirect/Connect64_for_ODBC_71/bin
    ./ddtestlib ddgplm27.so

You should receive output 
*Load of ddgplm27.so successful, qehandle is 0x2105F00*
*File version: 07.16.0389 (B0562, U0408)*

**RUN ON GREENPLUM MDW SERVER ("GUEST" IN VAGRANT)**

**RUN AS GPADMIN USER(i.e., "sudo su gpadmin" and execute subsequent commands)**

Add/modify the following variables to .bashrc variables for the gpadmin user:

    export PGPORT=5432
    export PGUSER=gpadmin
    export PGPASSWORD=gpadmin
    export PGDATABASE=development

Modify the Postgres pg_hba.conf file to allow any incoming connections.
(Not congruent with security best practices for a production environment!)
 
    vi $MASTER_DATA_DIRECTORY/pg_hba.conf 

Add the following line and exit:

    host all all all trust

Source in new variables and restart Greenplum:

    . ~/.bashrc
    gpstop -ra

**RUN ON HOST (I.E. LOCAL SERVER)**

If desired, test accessibility via database IDE if desired. (DBeaver with JDBC driver was used for this test).
The following parameters work with antecedent Vagrant cluster install:
Host: **192.168.0.200**
Database: **development**
Username: **gpadmin**
Password: **gpadmin**

Last of all, run some verification tests using Progress' validation scripts.
These are most likely superfluous if you already can connect with a database IDE, but they're included in
the Progress documentation so I'm including them here for posterity.

    cd /opt/Progress/DataDirect/Connect64_for_ODBC_71/samples/example
    ./example

Enter the bolded text when prompted:

    Enter the data source name : Greenplum Wire Protocol
    Enter the user name        : gpadmin
    Enter the password         : gpadmin

    Enter SQL statements (Press ENTER to QUIT)
    SQL> select version();
    
You should received output like the following:
*version    
PostgreSQL 9.4.24 (Greenplum Database 6.14.0 build commit:62d24f4a455276cab4bf2ca4538e96dcf58db8ba Open Source) on x86_64-unknown-linux-gnu, compiled by gcc (GCC) 6.4.0, 64-bit compiled on Feb  5 2021 18:58:52*

Check the installation of ODBC.  You should now see output like the following:

    odbcinst -j

*unixODBC 2.3.4
DRIVERS............: /etc/odbcinst.ini
SYSTEM DATA SOURCES: /etc/odbc.ini
FILE DATA SOURCES..: /etc/ODBCDataSources
USER DATA SOURCES..: /opt/Progress/DataDirect/Connect64_for_ODBC_71/odbc.ini
SQLULEN Size.......: 8
SQLLEN Size........: 8
SQLSETPOSIROW Size.: 8*

Validate the ODBC information again [we will use this for the pyodbc setup]

    odbcinst -q -s

*[ODBC]
[Greenplum Wire Protocol]*

If there are issues, I have enclosed the output of all of my odbc-related configs at the end of this file.

At this point, you should have a working Greenplum instance that is accessible from your host via a database IDE.
The next step is to install pyodbc and test connectivity with a Python program.
This assumes previous python3 install (tested with 3.6.4).
Ensure Greenplum has started (gpstart command) before testing!

Install pyodbc and connecting to Greenplum. 
Install Quandl while we're at it:

    pip install pyodbc
    pip3 install quandl

Now test connecting to Greenplum. 
Copy this information into a file issue "chmod +x [filename]' python3 [filename]" to execute. 

    import pyodbc
  
    cnxn = pyodbc.connect('DRIVER={/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib/ddgplm27.so};'
    'LogonID=gpadmin;'
    'Password=gpadmin;'
    'Database=development;'
    'HostName=192.168.0.200;'
    'PortNumber=5432;')

    cursor = cnxn.cursor()
    cursor.execute("SELECT version() testfield")
    rows = cursor.fetchall()
    for row in rows:
        print(row.testfield)

You should receive the same output you received when using Progress' ODBC validation script.
At this point you can run the rest of the scripts 

## Installation (Apache MADlib machine learning library)

This installation assumes my previous Greenplum cluster build in the home directory of this
current user using Centos 7.
It could easily be modified to work on a regular Postgres instance.

Instructions based on those found on the Apache Wiki site and Pivotal documentation
If in doubt on one -- check the other!  And if it still doesn't work, it's probably not you.

https://cwiki.apache.org/confluence/display/MADLIB/Installation+Guide
https://gpdb.docs.pivotal.io/6-2/ref_guide/extensions/madlib.html

This presupposes that Greenplum has been started on the Vagrant cluster; ymmv if using
a different build.

Navigate to https://network.pivotal.io/products/pivotal-gpdb 
Download the MADLib binary under "Greenplum Advanced Analytics" (requires registration)
"MADlib 1.18.0+1 for RHEL 7" and copy the file to the gpadmin home directory
on Greenplum master node:

**ON HOST**

    cp ~/Downloads/madlib-1.18.0+1-gp6-rhel7-x86_64.tar.gz .
    scp madlib-1.18.0+1-gp6-rhel7-x86_64.tar.gz gpadmin@mdw:/home/gpadmin

ssh into master node on Vagrant cluster, extract & install MADLib library

    vagrant ssh mdw

**ON GREENPLUM MASTER NODE (GUEST) **

    sudo su gpadmin
    cd ~
    tar -xvf madlib-1.18.0+1-gp6-rhel7-x86_64.tar.gz 

MADlib tries to build a "madlib" schema in the default database directory in the next 
operation.  Provided you followed the previous instructions and set the PGDATABASE
environment variable in .bashrc, you should be OK.
If not, you need to issue "createdb" with no explicit database parameter in order to
bypass a potential "database "default_login_database_name" does not exist" error

    gppkg -i madlib-1.18.0+1-gp6-rhel7-x86_64/madlib-1.18.0+1-gp6-rhel7-x86_64.gppkg

Validate psql, postgres and pg_config are present

    which psql postgres pg_config
    
You should get output nearly identical to the following:
*/usr/local/greenplum-db-6.14.0/bin/psql
/usr/local/greenplum-db-6.14.0/bin/postgres
/usr/local/greenplum-db-6.14.0/bin/pg_config*


Ensure database started and running

    psql -c 'select version()'

You should get output nearly identical to the following:
*PostgreSQL 9.4.24 (Greenplum Database 6.14.0 build commit:62d24f4a455276cab4bf2ca4538e96dcf58db8ba Open Source) on x86_64-unknown-linux-gnu, compiled by gcc (GCC) 6.4.0, 64-bit compiled on Feb  5 2021 18:58:52*

Run MADlib deployment utility.
Note: Apache Wiki documentation states to run the following command which did not work for me.
(Perhaps for an older version of Greenplum?)
/usr/local/madlib/bin/madpack –p greenplum install 

Note: On the first attempt of this execution, I received a "madpack.py: ERROR : Failed executing m4"
error which was rectified by installing m4 and rerunning the install again:

    sudo yum install m4
    /usr/local/greenplum-db-6.14.0/madlib/Versions/1.18.0/bin/madpack -s madlib -p greenplum -c gpadmin@mdw:5432/testdb install

You should have received the following message:
*madpack.py: INFO : MADlib 1.18.0 installed successfully in madlib schema.*

# Create demo/test tables for data ingestion and to test MADlib functionality

Check installation of MADlib:

    /usr/local/greenplum-db-6.14.0/madlib/Versions/1.18.0/bin/madpack -p greenplum install-check

Create sample test table and run rudimentary linear regression algorithm on it.
Example from https://gpdb.docs.pivotal.io/6-13/analytics/madlib.html

    psql development 
 
Execute each of the following SQL DDL statements piecemeal to validate MADlib functionality
by performing a simple linear regression on a test table:

    CREATE TABLE regr_example (
     id int,
     y int,
     x1 int,
     x2 int
     );
  
    INSERT INTO regr_example VALUES
     (1,  5, 2, 3),
     (2, 10, 7, 2),
     (3,  6, 4, 1),
     (4,  8, 3, 4);
  
    SELECT madlib.linregr_train (
     'regr_example',         -- source table
     'regr_example_model',   -- output model table
     'y',                    -- dependent variable
     'ARRAY[1, x1, x2]'      -- independent variables
     );
  
    SELECT regr_example.*,
          madlib.linregr_predict ( ARRAY[1, x1, x2], m.coef ) as predict,
          y - madlib.linregr_predict ( ARRAY[1, x1, x2], m.coef ) as residual
    FROM regr_example, regr_example_model m;

The next table is necessary for the subsequent Quandl data ingestion.

    CREATE TABLE pd_pt_prices
    (id serial,
    closing_date date,
    pd_usd_am decimal,
    pd_usd_pm decimal,
    pd_eur_am decimal,
    pd_eur_pm decimal,
    pd_gbp_am decimal,
    pd_gbp_pm decimal,
    pt_usd_am decimal,
    pt_usd_pm decimal,
    pt_eur_am decimal,
    pt_eur_pm decimal,
    pt_gbp_am decimal,
    pt_gbp_pm decimal
    );


# Executing application

Once you have performed all of the requisite steps (pyodbc install, ODBC driver install, and validated connection to the target Greenplum database) execute the application in your source directory (ensure that you've replaced the stubbed-out Quandl API key with your own!)
 
    source /opt/Progress/DataDirect/Connect64_for_ODBC_71/odbc.sh
    ./gpdb_qpp_ml.py

## Executing Apache MADlib examples (OPTIONAL)

There are some trivial examples utilizing the test data with Apache MADlib in the *madlib_sample.sql* file.

# Tests

## Contributors

## License

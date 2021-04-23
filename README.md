# Quandl data ingestion into Greenplum database with pyodbc and subsequent analysis with Apache MADlib ML library
## Synopsis

This project is a tutorial detailing ingestion of financial data (using Quandl.com, which provides an exceptionally nice API with many free datasets) into a Greenplum database with pyodbc that can be subsequently analyzed/manipulated with the Apache MADlib ML library.

After setting up this project, the user will have a working knowledge of the following:

1. Ingesting data into a Pandas dataframe from a Web API;
2. Performing basic transformations on Pandas data;
3. Establishing database connectivity via ODBC drivers in Python;
4. Insertion of data into a target database;
5. Installation of Apache MADlib machine learning package and basic manipulation of extracted/transformed/loaded Quandl data.

For this example, we are using palladium and platinum prices.

## Motivation

The initial inspiration for this project came from the investor James Dines' "wolfpack theory", which states that commodities typically move in "complexes".  The author was interested to see what the relationship was between the transition metals complex (i.e., palladium and platinum.)

There is often a dearth of "soup to nuts" tutorials and beginners are often left to the frustrating effort of (in this case) trying to piece together disparate pieces of a puzzle including database setup, ODBC configuration, Python code, and ancillary packages and installations.  

The purpose is to tie together an entire flow from ingesting a data source (from Quandl.com) into a Pandas dataframe, doing a couple of rudimentary manipulations on it, inserting it into the database, and showing how it can be subsequently manipulated with the Apache MADlib machine learning library.  I've included a lot of low-level detail on each step that will hopefully save someone quite a bit of time; the only downside is that a good chunk of the prerequisite installation steps aren't totally amenable to automation thanks to things like Pivotal requiring registration the requisite binaries.  

## Prerequisites (Hardware)

This project assumes that the user is running a Greenplum cluster per the author's previous installation (see https://github.com/jonathan-armstrong-303/vagrant_greenplum_6-1-4_install) in the Vagrant environment.  Greenplum's installation proved to be a bit... "opaque", but I was able to successfully create a nearly-100% automated build in the Vagrant environment, so the user shouldn't be intimidated by what would otherwise be the extremely esoteric installation process.  This installation could undoubtedly be easily extrapolated to just run on a local Postgres instance.

This was performed on my home Linux desktop (4 cores/4.2 GHz processors/64 GB memory) and allocated 12GB RAM to each of the four Greenplum nodes in Vagrant (admittedly 4GB less than the minimum recommended) running Ubuntu 20.04.

# Installation (Overview)

Before proceeding, the user needs to register at both the VMWare Tanzu website (for Greenplum binaries) as well as Quandl (for access to the Quandl API which is used to ingest the palladium/platnium price dataset in the example).  
 
https://login.run.pivotal.io/login

https://www.quandl.com/

There are two main sections to the installation section: installing the pyodbc package and ODBC files in order to connect to the Greenplum (or potentially Postgres) database from the host system, and installation of the Apache MADlib machine learning library (The MADlib install isn't necessary to get this code working and can be skipped if desired).

## Installation [pyodbc and Progress ODBC driver]

Before proceeding, ensure that instructions are issued on the appropriate server (i.e., host (i.e., local machine) or guest [i.e., Greenplum master node]).  This is explicitly noted in **BOLDED ALL CAPS** throughout the installation instruction.

**RUN ON HOST (i.e. local server)**

**INSTALLING THE DRIVER AND MODIFYING THE DSN**

Install the requisite unixodbc packages:

    sudo apt-get install -y unixodbc
    sudo apt-get install -y unixodbc-dev

Download and install the Progress ODBC driver.
This requires registration as stated in the parent "Installation" section.  (I tried to find a curl install and make this more automated to no avail.)
"Progress DataDirect Connect64 XE for ODBC for Pivotal Greenplum for Linux 64-bit"
https://network.pivotal.io/products/pivotal-gpdb#/releases/848083/file_groups/3302
Download the file from the website and extract: 

    cd ~/Downloads 
    tar -zxvf "PROGRESS_DATADIRECT_CONNECT64_ODBC_7.1.6+7.16.389.HOTFIX_LINUX_64.tar.gz"

Run dos2unix on the extracted script and also install ksh if needed (it was missing on Ubuntu 20.04).
Run dos2unix and also install Korn shell if necessary [it's missing on Ubuntu 20.04]:

    sudo apt install dos2unix
    dos2unix unixmi.ksh
    sudo apt install ksh

Create the necessary installation directory and make it universal read/write:

    sudo mkdir -p /opt/Progress; sudo chmod 777 /opt/Progress

Run extracted Korn shell install script [in same directory you just executed the tar]
Mindlessly enter the usual Y/YES/etc registration/installation information when prompted 
(not included for brevity)

    cd ~/Downloads
    ./unixmi.ksh

Enter the following for *both* key & serial number:
(please refer to https://gpdb.docs.pivotal.io/6-15/datadirect/datadirect_ODBC_71.html for potential updates)

    1076681984

Change to newly installed ODBC directory and source in ODBC parameters:

    cd /opt/Progress/DataDirect/Connect64_for_ODBC_71/
    source odbc.sh

Modify the following parameters in the $ODBCINI file.  Note that the IP address is based on the author's previous Greenplum install -- YMMV in your environment:

    vi $ODBCINI
    
Effect the following parameter changes in $ODBCINI:
    
    LogonID=gpadmin
    Password=gpadmin
    Database=development
    HostName=192.168.0.200
    PortNumber=5432
    
Exit the file and validate the changes successfully made:

    egrep -i "database|hostname|portnumber|logonid|password" $ODBCINI|egrep -vi "keypassword|keystorepassword" 

Verify the driver version. You should receive output 
*Load of ddgplm27.so successful, qehandle is 0x2105F00*
*File version: 07.16.0389 (B0562, U0408)*

    cd /opt/Progress/DataDirect/Connect64_for_ODBC_71/bin
    ./ddtestlib ddgplm27.so


**RUN ON GREENPLUM [OR POSTGRES] MDW SERVER ("GUEST" IN VAGRANT)**

**RUN AS GPADMIN USER (i.e., "sudo su gpadmin" and execute subsequent commands)**

Sudo to user "gpadmin" and edit the .bashrc file:

    sudo su gpadmin
    vi ~/.bashrc

Add/modify the following variables to .bashrc variables for the gpadmin user and exit the file:

    export PGPORT=5432
    export PGUSER=gpadmin
    export PGPASSWORD=gpadmin
    export PGDATABASE=development

Modify the Postgres pg_hba.conf file to allow any incoming connections.
(Not congruent with security best practices for a production environment!)
 
    vi $MASTER_DATA_DIRECTORY/pg_hba.conf 

Add the following line to pg_hba.conf and exit:

    host all all all trust

Source in new variables and restart Greenplum to effect changes:

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

Enter the data source name : **Greenplum Wire Protocol**

Enter the user name        : **gpadmin**

Enter the password         : **gpadmin**

Enter SQL statements (Press ENTER to QUIT)
    SQL> **select version();**
    
You should receive output e.g., the following:
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

You should receive the following output:

*[ODBC]*

*[Greenplum Wire Protocol]*

If there are issues (and hopefully this work instruction has saved someone the headache of having to troubleshoot these) I have enclosed the output of all of my odbc-related configs at the end of this document.)

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

Navigate to https://network.pivotal.io/products/pivotal-gpdb, download the MADLib binary under "Greenplum Advanced Analytics" (requires registration) entitled "MADlib 1.18.0+1 for RHEL 7", and copy the file to the gpadmin home directory on Greenplum master node:

**ON HOST**

    cp ~/Downloads/madlib-1.18.0+1-gp6-rhel7-x86_64.tar.gz .
    scp madlib-1.18.0+1-gp6-rhel7-x86_64.tar.gz gpadmin@mdw:/home/gpadmin

ssh into master node on Vagrant cluster, extract & install MADLib library:

    vagrant ssh mdw

**ON GREENPLUM MASTER NODE (GUEST)**

    sudo su gpadmin
    cd ~
    tar -xvf madlib-1.18.0+1-gp6-rhel7-x86_64.tar.gz 

MADlib tries to build a "madlib" schema in the default database directory ($PGDATABASE) in the next operation.  Provided you followed the previous instructions and set the PGDATABASE environment variable in .bashrc, you should be OK. 

If not, you need to issue "createdb" with no explicit database parameter in order to bypass a potential "database "default_login_database_name" does not exist" error.

    gppkg -i madlib-1.18.0+1-gp6-rhel7-x86_64/madlib-1.18.0+1-gp6-rhel7-x86_64.gppkg

Validate psql, postgres and pg_config are present. 

You should get output nearly identical to the following:
*/usr/local/greenplum-db-6.14.0/bin/psql
/usr/local/greenplum-db-6.14.0/bin/postgres
/usr/local/greenplum-db-6.14.0/bin/pg_config*

    which psql postgres pg_config
    
Ensure database started and running.  

You should get output nearly identical to the following:
*PostgreSQL 9.4.24 (Greenplum Database 6.14.0 build commit:62d24f4a455276cab4bf2ca4538e96dcf58db8ba Open Source) on x86_64-unknown-linux-gnu, compiled by gcc (GCC) 6.4.0, 64-bit compiled on Feb  5 2021 18:58:52*

    psql -c 'select version()'

Run MADlib deployment utility.

Note: Apache Wiki documentation states to run the following command which did not work. (Perhaps for an older version of Greenplum?) */usr/local/madlib/bin/madpack –p greenplum install* Note: the "m4" install circumvents the "madpack.py: ERROR : Failed executing m4" error.  

You should have received the following message:
*madpack.py: INFO : MADlib 1.18.0 installed successfully in madlib schema.*

    sudo yum install m4
    /usr/local/greenplum-db-6.14.0/madlib/Versions/1.18.0/bin/madpack -s madlib -p greenplum -c gpadmin@mdw:5432/development install

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

The next table is necessary for the Quandl data ingestion found in the main project:

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

## APPENDIX -- ODBC-related file configuration output

Beginners will probably find the the installation process for ODBC drivers on Linux to be opaque and potentially tedious.  If you are having issues with the Greenplum installation (or other ODBC drivers) check all of your environment variables and various configuration files with odbcinst per the examples below.  The following output was present on my working configuration:  

    echo $ODBCINI $ODBCINST $LD_LIBRARY_PATH
    
/opt/Progress/DataDirect/Connect64_for_ODBC_71/odbc.ini 
/opt/Progress/DataDirect/Connect64_for_ODBC_71/odbcinst.ini 
/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib


    odbcinst -q -j
    
unixODBC 2.3.4
DRIVERS............: /etc/odbcinst.ini
SYSTEM DATA SOURCES: /etc/odbc.ini
FILE DATA SOURCES..: /etc/ODBCDataSources
USER DATA SOURCES..: /opt/Progress/DataDirect/Connect64_for_ODBC_71/odbc.ini
SQLULEN Size.......: 8
SQLLEN Size........: 8
SQLSETPOSIROW Size.: 8


    cat /etc/odbc.ini
    
[Greenplum Wire Protocol]
Driver=/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib/ddgplm27.so
Description=DataDirect 7.1 Greenplum Wire Protocol
LogonID=gpadmin
Password=gpadmin
Database=development
HostName=192.168.0.200
PortNumber=5432
DriverManagerEncoding=UTF-16


    cat /etc/odbcinst.ini
    
[Greenplum Wire Protocol]
Driver=/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib/ddgplm27.so
Setup=/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib/ddgplm27.so

    cat /opt/Progress/DataDirect/Connect64_for_ODBC_71/odbc.ini
[ODBC Data Sources]
Greenplum Wire Protocol=DataDirect 7.1 Greenplum Wire Protocol

[ODBC]
IANAAppCodePage=4
InstallDir=/opt/Progress/DataDirect/Connect64_for_ODBC_71
Trace=0
TraceFile=odbctrace.out
TraceDll=/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib/ddtrc27.so

[Greenplum Wire Protocol]
Driver=/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib/ddgplm27.so
Description=DataDirect 7.1 Greenplum Wire Protocol
LogonID=gpadmin
Password=gpadmin
Database=development
HostName=192.168.0.200
PortNumber=5432
DriverManagerEncoding=UTF-16

# Tests

## Contributors

## License

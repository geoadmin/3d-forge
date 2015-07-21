# 3d-forge
Read/Write quantized-mesh tiles

To clone use the --recursive option to get all submodules.
`git clone --recursive https://github.com/geoadmin/3d-forge`

## Getting started

    make all

## Interactive programming

    source venv/bin/activate
    ipython
    run {yourScript}.py

#### Enter debug mode

    %debug

#### Get the latest traceback

    %tb


## Styling

#### Check styling

    make lint

#### Fix styling (only pep8 errors)

    make autolint

### Copy a file to S3 from command line

    aws --profile tms3d_filestorage s3 cp layer.json  s3://tms3d.geo.admin.ch/

## Create 3d-tiling instance

- Create instance here: https://tilegenmanager.prod.bgdi.ch/index/index

- Connect to created instance with user `tileforge`

- Adapt your configurations (.bashrc, .vim, .screenrc) if desired

- sudo su postgres

  * edit `/etc/postgresql/9.1/main/postgresql.conf`

  * uncommend `ssl=true` line

  * restart postgresql with `/etc/init.d/postgresql restart`

  * connect to postgress with `psql postgres`

  * change passwrod to xxx with \password

  * exit sudo

- add credentials to .boto file

- add configuration to .aws/config

- add credentials to .aws/credentials

- mount zadara with `sudo -u root /bin/mount /var/local/cartoweb`

- get project with `git clone --recursive https://github.com/geoadmin/3d-forge`

- install with `make install`

- create db with `make createdb`, adapt `database.cfg` for different data sets

- create tiles with `tmspyramid`, adapt `tms.cfg` for different tiler
  configurations

- you can also deactivate stats collection by setting `track_activities` to off in `/etc/postgresql/9.1/main/postgresql.conf`

## Remove logs

    rm -f /var/log/tileforge/*.log

    sudo su postgres

    rm -r /var/log/postgresql/*

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

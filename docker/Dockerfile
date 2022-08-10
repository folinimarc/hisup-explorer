# docker rmi ubu -f && docker image build -t ubu --file Dockerfile ../ && docker run -it -p 8000:8000 --rm ubu


# Thanks: https://towardsdatascience.com/conda-pip-and-docker-ftw-d64fe638dc45
FROM ubuntu:18.04

SHELL [ "/bin/bash", "--login", "-c" ]

# Create a non-root user
ARG username=laiskasiili
ARG uid=1000
ARG gid=100
ENV USER $username
ENV UID $uid
ENV GID $gid
ENV HOME /home/$USER
RUN adduser --disabled-password \
    --gecos "Non-root user" \
    --uid $UID \
    --gid $GID \
    --home $HOME \
    $USER

# install system dependencies (still as root)
RUN apt-get update && apt-get install -y curl wget jq git build-essential

# create a project directory inside user home
USER $USER
ENV PROJECT_DIR $HOME/app
RUN mkdir $PROJECT_DIR
WORKDIR $PROJECT_DIR
USER root

# clone HiSup repo
RUN git clone https://github.com/SarahwXU/HiSup.git
WORKDIR $PROJECT_DIR/HiSup
# make hisup package available for python import
ENV PYTHONPATH "${PYTHONPATH}:$PROJECT_DIR/HiSup"

# install miniconda
ENV MINICONDA_VERSION latest
ENV CONDA_DIR $HOME/miniconda3
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-$MINICONDA_VERSION-Linux-x86_64.sh -O ~/miniconda.sh && \
    chmod +x ~/miniconda.sh && \
    ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh
# make non-activate conda commands available
ENV PATH=$CONDA_DIR/bin:$PATH
# make conda activate command available from /bin/bash --login shells
RUN echo ". $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.profile
# make conda activate command available from /bin/bash --interative shells
RUN conda init bash

# build the conda environment
ENV ENV_PREFIX $PWD/env
RUN conda update --name base --channel defaults conda && \
    conda create --prefix $ENV_PREFIX python=3.7

# Install and compile hisup dependencies following
# https://github.com/SarahwXU/HiSup
RUN conda activate $ENV_PREFIX && \
    conda install -y conda-build pytorch==1.7.0 torchvision==0.8.0 cudatoolkit=11.0 -c pytorch && \
    conda develop . && \
    pip install -r requirements.txt && \
    cd hisup/csrc/lib &&  \
    make && \
    conda deactivate

# install CUDA (needed for hisup)
RUN apt-get install -y software-properties-common \
    && add-apt-repository ppa:graphics-drivers/ppa \
    && apt-get update \
    && apt-get install -y ubuntu-drivers-common
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
RUN ubuntu-drivers autoinstall \
    && apt install -y nvidia-cuda-toolkit

# install python packages
RUN conda activate $ENV_PREFIX && \
    # packages related to web app
    pip install django djangorestframework gunicorn celery psycopg2-binary flower redis && \
    # packages related to footprint hisup pre- and postprocessing
    pip install numpy shapely pygeos pyproj geopandas && \
    conda deactivate

# copy entrypoint and django project
COPY docker/entrypoint_django.sh /usr/local/bin/
RUN chown $UID:$GID /usr/local/bin/entrypoint_django.sh && \
    chmod u+x /usr/local/bin/entrypoint_django.sh
COPY docker/entrypoint_celery.sh /usr/local/bin/
RUN chown $UID:$GID /usr/local/bin/entrypoint_celery.sh && \
    chmod u+x /usr/local/bin/entrypoint_celery.sh
COPY django $PROJECT_DIR/django
RUN chown -R $UID:$GID $PROJECT_DIR

USER $USER
WORKDIR $PROJECT_DIR/django/footprint_service
# ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]
# CMD ["gunicorn" ,"--workers", "2", "--threads", "2", "--bind", "0.0.0.0:8000", "main.wsgi"]

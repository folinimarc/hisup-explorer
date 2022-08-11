FROM continuumio/miniconda3:4.12.0

SHELL [ "/bin/bash", "--login", "-c" ]

# Create a non-root user
ENV APP_HOME /home/app
ENV UID 1000
ENV GID 100
RUN mkdir -p $APP_HOME
RUN adduser --disabled-password \
    --gecos "Non-root user" \
    --uid $UID \
    --gid $GID \
    --home $APP_HOME \
    app

# install system dependencies.
# libgl1 seems to be a dependency for cv2 that needs to be installed extra when
# skipping the cuda installation.
RUN apt-get update && apt-get install -y git build-essential libgl1

# build the conda environment
ENV ENV_PREFIX $APP_HOME/env
RUN conda update --name base --channel defaults conda && \
    conda create --prefix $ENV_PREFIX python=3.7

# clone HiSup repo
WORKDIR $APP_HOME
RUN git clone https://github.com/SarahwXU/HiSup.git
# make hisup package available for python import
ENV PYTHONPATH "${PYTHONPATH}:$APP_HOME/HiSup"


# # install CUDA, needed for hisup training (?)
# RUN apt-get install -y software-properties-common \
#     && add-apt-repository ppa:graphics-drivers/ppa \
#     && apt-get update \
#     && apt-get install -y ubuntu-drivers-common
# ENV LC_ALL C.UTF-8
# ENV LANG C.UTF-8
# RUN ubuntu-drivers autoinstall \
#     && apt install -y nvidia-cuda-toolkit


# Install and compile hisup dependencies following
# https://github.com/SarahwXU/HiSup
# Excluded for now: cudatoolkit=11.0
WORKDIR $APP_HOME/HiSup
RUN conda activate $ENV_PREFIX && \
    conda install -y conda-build pytorch==1.7.0 torchvision==0.8.0 -c pytorch && \
    conda develop . && \
    pip install -r requirements.txt && \
    cd hisup/csrc/lib &&  \
    make && \
    conda deactivate


# install python packages
RUN conda activate $ENV_PREFIX && \
    # packages related to web app
    pip install django djangorestframework gunicorn celery psycopg2-binary flower redis && \
    # packages related to footprint hisup pre- and postprocessing
    pip install numpy shapely pygeos pyproj geopandas && \
    conda deactivate

# copy entrypoint scripts
COPY entrypoint_django_dev.sh /usr/local/bin/
RUN chown $UID:$GID /usr/local/bin/entrypoint_django_dev.sh && \
    chmod u+x /usr/local/bin/entrypoint_django_dev.sh
COPY entrypoint_django_prod.sh /usr/local/bin/
RUN chown $UID:$GID /usr/local/bin/entrypoint_django_prod.sh && \
    chmod u+x /usr/local/bin/entrypoint_django_prod.sh
COPY entrypoint_celery.sh /usr/local/bin/
RUN chown $UID:$GID /usr/local/bin/entrypoint_celery.sh && \
    chmod u+x /usr/local/bin/entrypoint_celery.sh
# copy django project
COPY src $APP_HOME/src
RUN chown -R $UID:$GID $APP_HOME/src
# Create folder for staticfiles
RUN mkdir $APP_HOME/staticfiles
RUN chown -R $UID:$GID $APP_HOME/staticfiles
# Copy nginx config file to image. This will be shared with
# nginx image via shared volume.
RUN mkdir $APP_HOME/nginx
RUN mkdir $APP_HOME/nginx_mount
COPY nginx.conf $APP_HOME/nginx/
# Give all permissions to non root user
RUN chown -R $UID:$GID $APP_HOME/nginx
RUN chown -R $UID:$GID $APP_HOME/nginx_mount


# Clean up
RUN apt purge -y git build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR $APP_HOME/src
USER $USER

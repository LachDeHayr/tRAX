#TRAX Dependencies Dockerfile
# - Python 2.7
# - Pysam 0.12 Python library (Older versions have a memory leak, make sure you have an updated version)
# - bowtie2 3.5.1
# - Samtools 1.9
# - R 3.5.1
# - Deseq2 R library
# - getopt R library
# - ggplot2 R library
# - Infernal 1.1 or higher
# - The TestRun.bash script requires the SRA toolkit(fastq-dump) and cutadapt to function

# Use Ubuntu image because of the flexibility
FROM ubuntu:16.04
ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

# Change to root user for install and compiling of packages
USER root

# Pre-requisites, Python2.7, and SRA-Toolkit
RUN apt-get update && apt-get install -yq --no-install-recommends \
    apt-utils \
    apt-transport-https \
    aptitude \
    bowtie2 \
    build-essential \
    ca-certificates \
    curl \
    dirmngr \
    fort77 \
    gcc-multilib \
    gfortran \
    git \
    gobjc++ \
    # gpg-agent \
    gsl-bin \
    python \
    python-pip \
    software-properties-common \
    sra-toolkit \
    wget \
    xorg-dev \
    zlib1g-dev

RUN apt-get update && apt-get install -yq --no-install-recommends \
    libblas-dev \
    libbz2-1.0 \
    libbz2-dev \
    libbz2-ocaml \
    libbz2-ocaml-dev \
    libudunits2-dev \
    libcairo2-dev \
    libcurl4-openssl-dev \
    libgsl0-dev \
    liblzma-dev \
    libncurses5-dev \
    libreadline-dev \
    libssh2-1-dev \
    libssl-dev \
    libxml2-dev

RUN apt-get update && apt-get install -yq --no-install-recommends \
    libgit2-dev

# Install Pysam and Cutadapt
RUN pip install --upgrade pip
RUN pip install setuptools
RUN pip install pysam==0.12 cutadapt

# Install SAMTools
RUN curl -fsSL https://github.com/samtools/samtools/releases/download/1.9/samtools-1.9.tar.bz2 -o /opt/samtools-1.9.tar.bz2 && \
    tar xvjf /opt/samtools-1.9.tar.bz2 -C /opt/ && \
    cd /opt/samtools-1.9 && \
    ./configure && \
    make && \
    make install && \
    rm /opt/samtools-1.9.tar.bz2

# Install Infernal 1.1.2
RUN curl -fsSL http://eddylab.org/infernal/infernal-1.1.2-linux-intel-gcc.tar.gz -o /opt/infernal-1.1.2.tar.gz && \
    tar xvzf /opt/infernal-1.1.2.tar.gz -C /opt/ && \
    cd /opt/infernal-1.1.2-linux-intel-gcc && \
    ./configure && \
    make && \
    make check && \
    make install && \
    rm /opt/infernal-1.1.2.tar.gz

# Change user to install R packages to correct directory/project
USER $NB_UID

# Install R-3.5.3 and CRAN recommended packages
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9 && \
    add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu xenial-cran35/'
RUN apt-get update && apt-get install -yq --no-install-recommends r-base-dev=3.5.1-1xenial

# Install Getopt, GGplot2, BiocManager and DESeq2
RUN Rscript -e 'install.packages("getopt", dependencies=TRUE, lib="/usr/local/lib/R/site-library")'
RUN Rscript -e 'update.packages()'
RUN Rscript -e 'install.packages("ggplot2", dependencies=TRUE, lib="/usr/local/lib/R/site-library")'
RUN Rscript -e 'install.packages("BiocManager")'
RUN Rscript -e 'BiocManager::install(c("DESeq2"))'

#Set working directory and copy TRAX software into docker container
COPY * /trax/
RUN chmod -R 777 /trax/
WORKDIR /trax/

###################################
### FOR BULDING FROM SOURCE USE ###
###################################

# Install Python 2.7 in the future when Ubuntu changes versions
#RUN curl -fsSL https://www.python.org/ftp/python/2.7.16/Python-2.7.16.tgz  -o /opt/Python-2.7.16.tgz && \
#    tar xvzf /opt/Python-2.7.16.tgz -C /opt/ && \
#    cd /opt/Python-2.7.16 && \
#    ./configure --enable-optimizations && \
#    make && \
#    make install && \
#    rm /opt/Python-2.7.16.tgz

# Install Bowtie2
#RUN curl -fsSL https://github.com/BenLangmead/bowtie2/archive/v2.3.5.1.tar.gz -o /opt/bowtie2-3.5.1.tar.gz && \
#    tar xvzf /opt/bowtie2-3.5.1.tar.gz -C /opt/ && \
#    ls /opt/ && \
#    cd /opt/bowtie2-3.5.1 && \
#    ./configure && \
#    make && \
#    make install && \
#    rm /opt/bowtie2-3.5.1.tar.gz

# Install R-3.5.1
#RUN curl -fsSL https://cloud.r-project.org/bin/linux/ubuntu/bionic-cran35/r-base_3.5.3.orig.tar.gz -o /opt/r-base_3.5.3.orig.tar.gz && \
#    tar xzf /opt/r-base_3.5.3.orig.tar.gz -C /opt/ && \
#    cd /opt/R-3.5.3 && \
#    ./configure --with-readline=no --with-x=no --enable-utf8 --enable-unicode-properties && \
#    make && \
#    make install && \
#    rm /opt/r-base_3.5.3.orig.tar.gz

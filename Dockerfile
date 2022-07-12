FROM continuumio/miniconda3

WORKDIR /src/teal

COPY environment.yml /src/teal/

RUN conda install -c conda-forge gcc python=3.10 \
    && conda env update -n base -f environment.yml

COPY . /src/teal

RUN pip install --no-deps -e .

FROM continuumio/miniconda3

WORKDIR /src/emohawk

COPY environment.yml /src/emohawk/

RUN conda install -c conda-forge gcc python=3.10 \
    && conda env update -n base -f environment.yml

COPY . /src/emohawk

RUN pip install --no-deps -e .

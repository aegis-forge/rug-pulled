FROM continuumio/miniconda3:v25.11.1

WORKDIR /app

COPY . .

# Create environment
RUN conda env create -f environment.yml

# Activate the conda environment
SHELL ["conda", "run", "-n", "rug-pulled", "/bin/bash", "-c"]

EXPOSE 8501

ENTRYPOINT ["conda", "run", "-n", "rug-pulled", "streamlit", "run", "main.py"]

FROM continuumio/miniconda3:25.1.1-0

WORKDIR /app

COPY . .

# Create environment
RUN conda env create -f environment.yml

# Activate the conda environment
SHELL ["conda", "run", "-n", "kleio", "/bin/bash", "-c"]

# Expose port, healthcheck and start service
EXPOSE 8501

ENTRYPOINT ["conda", "run", "-n", "kleio", "streamlit", "run", "main.py"]

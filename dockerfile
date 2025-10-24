FROM continuumio/miniconda3:25.3.1-1

WORKDIR /app

# Create environment
COPY environment.yml .
RUN conda env create -f envirnment.yml

# Activate the conda environment
RUN conda activate kleio

# Expose port, healthcheck and start service
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

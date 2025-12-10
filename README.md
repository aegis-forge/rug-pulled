<p align="center">
  <img width="100" src="static/vectors/logo-full.svg" alt="kleio logo"> <br><br>
  <img src="https://img.shields.io/badge/streamlit-v1.50.0-red" alt="Go version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

# kleio-webapp

## Export Conda Dependencies

```sh
conda env export --no-builds | grep -v "^prefix: " > environment.yml
```

## Install Conda Dependencies

```sh
conda env create -f environment.yml
```

## Run App

```sh
streamlit run ./src/main.py
```

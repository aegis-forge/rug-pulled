# rug-pulled

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

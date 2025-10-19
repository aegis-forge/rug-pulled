# kleio-webapp

## Export Conda Dependencies

```sh
conda env export --no-builds | grep -v "^prefix: " > environment.yml
```

## Run App

```sh
streamlit run ./src/main.py
```

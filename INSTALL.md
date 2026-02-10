## Installation

### Docker

To easily use Kleio and its webapp, we provided a Dockerfile for each component, as well as two Docker compose files. There are two ways in which the webapp can be used to display the data. You can have it display pre-computed repositories (the dataset that has been used in the "Changing Nothing, Yet Changing Everything: Exploring Rug Pulls in GitHub Workflows" paper), or by pulling custom data directly from the Kleio database.

### Using Pre-computed Data

If you want to see the plots and statistics of the paper, you should use the pre-computed data that we provide (see the `Dataset` section in `README.md`). Now, you have two ways to set up and launch the webapp, by locally running the Python server, or by using the Dockerfile.

To run the webapp using Python, run the following commands (please note that you should have [conda](https://www.anaconda.com/download) installed on your system)

```sh
# Install the dependencies and activate the environment
conda env create -f environment.yml
conda activate rug-pulled

# Start the server (a browser page will be automatically opened)
streamlit run main.py
```

To run the webapp using Docker, run the following command (please note that you should have [docker](https://www.docker.com/) installed on your system)

```sh
# Build the webapp image
docker build -t rug-pulled .
# Run the Docker compose file
docker compose -f compose.yml up -d
```

Once the server or Docker container is up, navigate to the link [http://localhost:8501](http://localhost:8501)

### Using Custom Data

If you want to visualize plots and statistics for a custom set of repositories, then you will need to use the `compose-full.yml` Docker compose file. It is not recommended to manually setting up the single components. Before running the installation commands, be sure to do the following:

1. Copy the `.env.template` file and rename it to `.env`. This file will be used by Docker compose later.

2. Create a `repositories.txt` file in the root of this repository. The structure of the file should be as follows (be sure to add a newline at the end of the file):

```
https://github.com/aegis-forge/soteria
https://github.com/aegis-forge/cage
https://github.com/aegis-forge/kleio

```

3. If any of the repositories are private (or to have a higher rate limit on GitHub's API), create a [GitHub PAT](https://github.com/settings/personal-access-tokens) and place it in the `.env` file you created in step 1. 

4. Now that the setup is complete, you can run the following Docker installation commands (please note that you should have [docker](https://www.docker.com/) installed on your system):

```sh
# Build the webapp image
docker build -t rug-pulled .
# Run the Docker compose file
docker compose -f compose-full.yml up -d
```

5. Once the crawler is done, create the data files necessary for the webapp to display the data. To do so, run the methods in `src/scripts.py`. Once the `data/` directory has been created and populated, you'll be able to visualize it in the webapp (navigate to [http://localhost:8501](http://localhost:8501)).

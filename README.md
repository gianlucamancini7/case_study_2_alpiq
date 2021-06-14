A Study on Intraday Lead-Time CH-DE Electricity Market Variation
==============================

### ALPIQ Case Study: Investigating the impact of lead-time to gate closure reduction time for the Swiss and German intraday market

This repository summarizes the study carried out in the context of the Case Study project in the Master of Energy Science and Technology at ETH Zurich in collaboration with Alpiq. The study explores the effect that reducing the lead time to gate closure for Swiss-German transaction on the intraday market from 1 hour to 30 minutes would have for the German market and for the Swiss flexible hydro assets. 

#### How to use the repo
In order to be able to use, re-use or develop further this repo, it is necessary to have *python 3.8* installed on your machine. You can easily download a python version [here](https://www.python.org/downloads/) or download the [Anaconda](https://docs.anaconda.com/anaconda/install/) version to easily use the [Anaconda Prompt](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html)

#### Get started

Clone the github repository in the on your preferred computer location. Otherwise, download the ZIP version of the code from the dropdown button.
```
git clone https://github.com/gianlucamancini7/case_study_2_alpiq.git
```
Navigate inside your repository from the terminal as follows:
```
cd case_study_2_alpiq
```
Once in the folder, create a [conda](https://salishsea-meopar-docs.readthedocs.io/en/latest/work_env/python3_conda_environment.html) or a virtual environment as shown below.
```
conda create --name env python=3.8
```
or 
```
python3 -m venv env
```

Activate the environment before starting to code or to use the dashboard.
```
source env/bin/activate
```
or with the following in case you have chosen for Conda as shown in the guide accessible through the hyperlink above.
```
source activate env
```
Finally install the requirements needed.

```
pip install -r requirements.txt
```

And you should be good to go and start exploring the code!

#### Dashboard
To use the dashboad it is important not to change the file structure in the ```data``` folder. The dashboard works locally on your computer and it serves as a visualization and exploration tool based on the processed data obtained in the analysis. To use the dashboard run the following from the terminal or anaconda prompt:

```
cd dash_board/
python app_complete.py
```
Then navigate to http://127.0.0.1:8050/ on your web-browser and start using the app.


Project Organization
------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources such as EPEX limit order book
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── bin                <- Executable Python scripts which are to be used to effectively process the data
    │                         and perform the model calculations on the whole dataset.
    │ 
    ├── dash_board         <- Location of dash-plotly dashboard usable to explore and study the processed 2019 EPEX transactions
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │          
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
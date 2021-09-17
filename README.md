# Ontology Mapping Exercise

This repository is a programming exercise whose aim it is to map ontology terms and ids when given an existing ontology file. Documentation will exist in this README, and a Jupyter Notebook within the folder `/documentation/` will walk through the whole exerecise. The standalone script is called `exercise.py` 

### Original Exercise Prompt 

* The task is to write a script / a set of scripts in Python 3.x that takes an ontology file as an input and  provides a table with mappings for each concept to terms from specified ontologies. 

The script(s) should do the following steps: 
  1. Read in the provided sample turtle file 
  2. Load into an appropriate data structure
  3. Extract IDs and Preferred Labels (preferably using SPARQL) from concepts **only in the “skin cancer” branch!**
  4. For each concept, retrieve mappings (using APIs)
  5. Write the combined result into a tab delimited file, in which you list the mappings you retrieved for the different target ontologies using the different methods. One line per concept. Use ‘;’ for concatenating multiple mappings into one field – if applicable
* A sample output file could look like this: 


| Concept | PT | OLS_mappings | OXO_mappings |
| ------- | -- | ------------ | ------------ | 
| DOID:162 | cancer | MeSH:D009369; EFO:0000311 | MeSH:D009369; EFO:0000311 |


### How to run `exercise.py`
This script was run using Anaconda. You will need the same environment to run the script.  
Steps to run the script: 
* Install [Anaconda for Python 3.8](https://www.anaconda.com/products/individual-d). 
* Then, on the command line run:  
```conda env create -f environment.yml```
* Make sure you `conda activate` the environment you just created
* Run the python program as usual:  
```python exercise.py```


### Additional info: the package `rdfpandas` 

The `pandas` package of course has many built-in functions to convert csv and other delimited data to DataFrames. But it does not handle RDF serializations well.  

The `rdfpandas` package addresses this issue by being able to handle Turtle RDF files, which is the file we are using in this exercise.  

```python
from rdfpandas.graph import to_dataframe
import pandas as pd
import rdflib

g = rdflib.Graph()
g.parse('to_df_test.ttl', format = 'ttl')
df = to_dataframe(g)
df.to_csv('test.csv', index = True, index_label = "@id")
```

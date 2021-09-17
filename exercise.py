#!/usr/bin/env python

import rdflib
from rdflib.plugins.sparql.processor import SPARQLResult
from rdfpandas.graph import to_dataframe
import pandas as pd
from pandas import DataFrame
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import urllib
import json
import os

# Change directories to /input/ 
os.chdir('input')

# Make the Turtle file into a DataFrame
g = rdflib.Graph()
g.parse('programming_exercise.skos.ttl', format = 'ttl')
df = to_dataframe(g)

# Query via SPARQL on our Turtle file
results = g.query("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT ?concept ?label
    WHERE {
    
    ?concept skos:prefLabel ?label .
    ?concept skos:broader* <http://purl.obolibrary.org/obo/DOID_4159> .
    }
""")

# Define our function to store the SPARQLResult object in a DataFrame
def sparql_results_to_df(results: SPARQLResult) -> DataFrame:
    """
    Export results from an rdflib SPARQL query into a `pandas.DataFrame`,
    using Python types. See https://github.com/RDFLib/rdflib/issues/1179.
    """
    return DataFrame(
        data=([None if x is None else x.toPython() for x in row] for row in results),
        columns=[str(x) for x in results.vars],
    )

# Use our function to produce the DataFrame
df1 = sparql_results_to_df(results)
# Do some regex to get rid of hyperlinks and replace underscores with colons
df1['concept'] = df1['concept'].str.replace(r'_', ':', regex=True)
df1['concept'] = df1['concept'].str.replace(r'^http://purl.obolibrary.org/obo/', '', regex=True)

# Set up some variables to prep for API calls
labels = df1['label']
ids = df1['concept']

# API call to MONDO using labels to search
iris = []
for label in labels:
    encodedLabel = urllib.parse.quote(label)
    url = "http://www.ebi.ac.uk/ols/api/select?q="+encodedLabel+"&queryFields=label&ontology=mondo&fieldList=id,iri,label,score,synonym"
    response = requests.get(url).json()
    if response['response']['numFound'] == 1:
        iri_hit = [i['iri'] for i in response["response"]["docs"]]
        iri_hit = str(iri_hit)[2:-2]
        iris.append(iri_hit.replace("http://purl.obolibrary.org/obo/", ""))
    elif response['response']['numFound'] > 1:
        iri_hits = [i['iri'] for i in response["response"]["docs"]]
        iri_hit = iri_hits[0]
        iris.append(iri_hit.replace("http://purl.obolibrary.org/obo/", ""))
    else:
        iri_hit = "No result"
        iris.append(iri_hit)

# Add results to new column in DataFrame        
df1['MONDO_IRI'] = iris

# API call to EFO ontology using labels to search
iris = []
for label in labels:
    encodedLabel = urllib.parse.quote(label)
    url = "http://www.ebi.ac.uk/ols/api/select?q="+encodedLabel+"&queryFields=label&ontology=efo&fieldList=id,iri,label,score,synonym"
    response = requests.get(url).json()
    if response['response']['numFound'] == 1:
        iri_hit = [i['iri'] for i in response["response"]["docs"]]
        iri_hit = str(iri_hit)[2:-2]
        iris.append(iri_hit.replace("http://www.ebi.ac.uk/efo/", ""))
    elif response['response']['numFound'] > 1:
        iri_hits = [i['iri'] for i in response["response"]["docs"]]
        iri_hit = iri_hits[0]
        iris.append(iri_hit.replace("http://www.ebi.ac.uk/efo/", ""))
    else:
        iri_hit = "No result"
        iris.append(iri_hit)

# Add results to new column in DataFrame
df1['EFO_IRI'] = iris
# Replace any duplicate hits EFO returned with MONO URIs
df1['EFO_IRI'] = df1.EFO_IRI.str.replace(r'^http://purl.obolibrary.org/obo/.+', r'No result', regex=True)
# Join MONDO and EFO mappings separated by a semi-colon, also drop duplicate No results
df1["OLS_Mappings"] = df1[['MONDO_IRI', 'EFO_IRI']].agg('; '.join, axis=1)
df1['OLS_Mappings'] = df1['OLS_Mappings'].str.replace('No result; ', '')
df1['OLS_Mappings'] = df1['OLS_Mappings'].str.replace('; No result', '')

# API call to OXO mappings service using IDs
meshes = []
efos = []
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

for i in ids:
    url = "https://www.ebi.ac.uk/spot/oxo/api/mappings?fromId="+i
    response = session.get(url).json()
    try:
        mesh_hits = [i['toTerm']['curie'] for i in response['_embedded']['mappings'] if i['toTerm']['datasource']['prefix'] == 'MeSH']
        efo_hits = [i['fromTerm']['curie'] for i in response['_embedded']['mappings'] if i['fromTerm']['datasource']['prefix'] == 'EFO']
        efo_hits = str(efo_hits)[2:-2]
        meshes.append(mesh_hits[0])
        efos.append(efo_hits)
    except:
        meshes.append('No result')
        efos.append('No result')

# Add results to new column in DataFrame
df1['MESH_ID'] = meshes
df1['EFO_ID'] = efos
# Join those columns into new column in DataFrame, also drop duplicate No results
df1["OXO_Mappings"] = df1[['MESH_ID', 'EFO_ID']].agg('; '.join, axis=1)
df1['OXO_Mappings'] = df1['OXO_Mappings'].str.replace('No result; ', '')
df1['OXO_Mappings'] = df1['OXO_Mappings'].str.replace('; No result', '')

# Make final DataFrame by subsetting df1
df_final = df1[['concept', 'label', 'OLS_Mappings', 'OXO_Mappings']]

# Write out the CSV to /output/ directory
# WARNING: When opening file in spreadsheet software, be sure to de-select semicolons as delimiters in the preview window!
df_final.to_csv('../output/output.csv')
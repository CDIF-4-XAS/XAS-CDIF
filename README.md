[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17421916.svg)](https://doi.org/10.5281/zenodo.17421916)

# Semantic description of XAS community standards using CDIF profile

This repository provides mapping of XAS community standards to the
[Cross-Domain Interoperability Framework
(CDIF)](https://cdif.codata.org/).  Version 1.0 corresponds to the
deliverable “D2: Semantic description of at least two XAS community
standards using a CDIF profile (XAS-CDIF)” of the
[CDIF-4-XAS](https://oscars-project.eu/projects/cdif-4-xas-describing-x-ray-spectroscopy-data-cross-domain-use)
project.

## Content

The covering document and the associated spreadsheet and other
materials present an initial attempt to take the major community
standards used for X-Ray Absorption Spectroscopy (XAS) and map them to
the standards recommended for cross-domain FAIR sharing of data by the
Cross Domain Interoperability Framework (CDIF) guidelines.  The
current standards landscape within the XAS community has been
extensively described in the document “Overview of X-Ray Absorption
Spectroscopy standards, vocabularies (and ontologies), data formats
and practices”.  This document builds on the analysis presented in
that document as a concrete exploration of how the data and metadata
from the two most common XAS standards can be expressed in a
CDIF-described package to facilitate use across domain, institutional,
and application boundaries.  It is felt that a concrete application of
the standards and guidelines involved will clearly indicate the next
steps for implementation.

While the focus of this document is technical, there are also
implications for how other activities by domain groups and standards
bodies can most effectively be conducted.  These implications can be
provided as feedback to various groups, and these will be mentioned
here.  The specific recommendations to be made to such groups do not,
however, form part of this deliverable, but will be formulated more
completely in other project deliverables in the future.

The full package comprises the following:

1. "CDIF-4-XAS: Mappings from Community Standards to CDIF": this
   document provides an overview for the mapping exercise.
   (`CDIF4XAS_Mappings_Intro_V1-FINAL_TEMPLATE.docx.pdf`)

2. XAS Data Interchange (XDI) Format Mapping to CDIF: this document
   shows how the different metadata fields in an XDI file are mapped
   into Schema.org per the CDIF recommendations.
   (`XDISpec-FieldsCDIF-Schema.orgMapping.docx`)

3. Example of XDI metadata in CDIF: This is a JSON-LD file formatted
   according to the CDIF recommendations, containing an example of XDI
   metadata.  (`se_na2so4-testschemaorg-cdiv3.jsonLD`)

4. Input XDI file: this is the XDI file used as the basis of the
   JSON-LD example in 3.  (`se_na2so4_rt.xdi`)

5. Mapping Spreadsheet for HDF5/NeXus/NXxas: This spreadsheet
   describes the mapping from HDF5 files created according to the
   NXxas profile of NeXus to CDIF-recommended standards.
   (`XAS-CDIFImplementation.xlsx`)

6. XAS Glossary Spreadsheet: this spreadsheet provides definitions and
   other information for a draft community glossary to support this
   mapping exercise.  (`XAS_Glossary.xlsx`)

7. XAS Glossary in SKOS: this files provides a machine-actionable
   version of the community glossary, to serve as an example of how
   the glossary could be published for FAIR purposes.
   (`XAS_Glossary_SKOS.json`)

## Copyright and License

The covering document is Copyright 2025 by its authors.  It is is
licensed under a [Creative Commons Attribution 4.0 International
License](https://creativecommons.org/licenses/by/4.0/).

The associated material is in the public domain.

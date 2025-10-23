# Semantic description of XAS community standards using CDIF profile

This repository provides mapping of XAS community standards to CDIF.
Version 1.0 corresponds to the deliverable “D2: Semantic description
of at least two XAS community standards using a CDIF profile
(XAS-CDIF)” of the CDIF-4-XAS project.

The package contains several files, each contributing different
information regarding a mapping from common X-Ray Absorption
Spectroscopy (XAS) data formats to the Cross Domain Interoperability
Framework (CDIF) recommended standards:

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
   mapping exercise.  (`XAS_Glossary.xslx`)

7. XAS Glossary in SKOS: this files provides a machine-actionable
   version of the community glossary, to serve as an example of how
   the glossary could be published for FAIR purposes.
   (`XAS_Glossary_SKOS.json`)

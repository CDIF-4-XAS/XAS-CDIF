#!/usr/bin/env python3
# >>> CDIF-SYNC GENERATED >>>
# GENERATED FILE -- DO NOT EDIT.
# Synced from CDIF/validation/tools/FrameAndValidate.py (the normative source).
# Edit there, then run:  python tools/sync_frameandvalidate.py --apply
# src-sha256: 16ff65c25c7aa5fc50fbf301ec317d5c5cb5b1649bafd4eca1a4a08dbac56a06
# <<< CDIF-SYNC GENERATED <<<

"""
CDIF JSON-LD Framing and Validation Script

Frames a CDIF JSON-LD document into a tree and validates it against a JSON
Schema. Works for any CDIF profile: the schema and frame default to the single
*Schema*.json / *-frame.jsonld found next to this script.

Usage:
    python FrameAndValidate.py <input.jsonld> [-o framed.json] [-v]
                               [--schema schema.json] [--frame frame.jsonld]
"""

import json
import argparse
import sys
from pathlib import Path
from pyld import jsonld
import jsonschema
from jsonschema import Draft202012Validator

# Configure the requests-based document loader
jsonld.set_document_loader(jsonld.requests_document_loader())

SCRIPT_DIR = Path(__file__).parent

# Properties that should always be arrays per the CDIF schemas. This is the
# UNION across all CDIF profiles -- wrapping a property that is absent from a
# given document is a harmless no-op, so one list serves every profile.
ARRAY_PROPERTIES = [
    # schema.org properties -- wrapped to array at any nesting level
    'schema:contributor',
    'schema:distribution',
    'schema:license',
    'schema:conditionsOfAccess',
    'schema:keywords',
    'schema:additionalType',
    'schema:sameAs',
    'schema:provider',
    'schema:funding',
    'schema:variableMeasured',
    'schema:spatialCoverage',
    'schema:temporalCoverage',
    'schema:relatedLink',
    'schema:hasPart',
    'schema:publishingPrinciples',
    'schema:potentialAction',
    'schema:httpMethod',
    'schema:contentType',
    'schema:query-input',
    'schema:participant',
    'schema:additionalProperty',
    # PROV properties
    'prov:wasGeneratedBy',
    'prov:wasDerivedFrom',
    'prov:used',
    # DQV properties
    'dqv:hasQualityMeasurement',
    # Dublin Core properties
    'dcterms:conformsTo',
    # DDI-CDI / CDIF data-description & data-structure properties (2026)
    'cdi:hasPhysicalMapping',
    'cdi:uses',
    'cdi:physicalDataType',
    'cdi:function',
    'cdi:takesSentinelValuesFrom',
    'cdi:statistic',
    'cdif:hasPhysicalMapping',
    'cdif:uses',
    'cdif:recommendedDataType',
    'cdif:isComposedOf',
    'cdif:has_Statistics',
    'cdif:has_CategoryStatistics',
    'cdif:appliesTo',
    'cdif:indexedBy',
    'cdif:statistics',
    # SKOS properties (codelist / conceptscheme profiles)
    'skos:hasTopConcept',
    'skos:inScheme',
    'skos:broader',
    'skos:narrower',
    'skos:related',
    'skos:broadMatch',
    'skos:narrowMatch',
    'skos:relatedMatch',
    'skos:exactMatch',
    'skos:closeMatch',
    'skos:altLabel',
    'skos:hiddenLabel',
    'skos:note',
    'skos:scopeNote',
    'skos:changeNote',
    'skos:editorialNote',
    'skos:historyNote',
    'skos:example',
]

# Properties that are arrays only in specific contexts (not globally) are handled
# via context-aware logic in remove_nulls_and_normalize():
# - schema:measurementTechnique: array at root, scalar inside variableMeasured
# - schema:encodingFormat: array on DataDownload/MediaObject, string on EntryPoint
# - schema:propertyID / schema:alternateName: array inside variableMeasured items

# Term mappings: unprefixed -> prefixed (to match schema expectations)
TERM_MAPPINGS = {
    'conformsTo': 'dcterms:conformsTo',
    'wasGeneratedBy': 'prov:wasGeneratedBy',
    'wasDerivedFrom': 'prov:wasDerivedFrom',
    'used': 'prov:used',
    'hasQualityMeasurement': 'dqv:hasQualityMeasurement',
    'isMeasurementOf': 'dqv:isMeasurementOf',
    'hasGeometry': 'geosparql:hasGeometry',
    'asWKT': 'geosparql:asWKT',
    'checksum': 'spdx:checksum',
    'algorithm': 'spdx:algorithm',
    'checksumValue': 'spdx:checksumValue',
    'hasBeginning': 'time:hasBeginning',
    'hasEnd': 'time:hasEnd',
    'inTimePosition': 'time:inTimePosition',
    'hasTRS': 'time:hasTRS',
    'numericPosition': 'time:numericPosition'
}

# Output context for compaction - uses explicit term mappings to avoid prefix conflicts
OUTPUT_CONTEXT = {
    # Namespace prefixes
    "schema": "http://schema.org/",
    "cdi": "http://ddialliance.org/Specification/DDI-CDI/1.0/RDF/",
    "csvw": "http://www.w3.org/ns/csvw#",
    "ada": "https://ada.astromat.org/metadata/",
    "xas": "https://ada.astromat.org/metadata/xas/",
    "nxs": "https://manual.nexusformat.org/classes/",

    # Explicit term mappings for other vocabularies (avoids prefix conflicts)
    "conformsTo": "http://purl.org/dc/terms/conformsTo",
    "wasGeneratedBy": "http://www.w3.org/ns/prov#wasGeneratedBy",
    "wasDerivedFrom": "http://www.w3.org/ns/prov#wasDerivedFrom",
    "used": "http://www.w3.org/ns/prov#used",
    "Activity": "http://www.w3.org/ns/prov#Activity",
    "hasQualityMeasurement": "http://www.w3.org/ns/dqv#hasQualityMeasurement",
    "isMeasurementOf": "http://www.w3.org/ns/dqv#isMeasurementOf",
    "QualityMeasurement": "http://www.w3.org/ns/dqv#QualityMeasurement",
    "hasGeometry": "http://www.opengis.net/ont/geosparql#hasGeometry",
    "asWKT": "http://www.opengis.net/ont/geosparql#asWKT",
    "wktLiteral": "http://www.opengis.net/ont/geosparql#wktLiteral",
    "checksum": "http://spdx.org/rdf/terms#checksum",
    "algorithm": "http://spdx.org/rdf/terms#algorithm",
    "checksumValue": "http://spdx.org/rdf/terms#checksumValue",
    "hasBeginning": "http://www.w3.org/2006/time#hasBeginning",
    "hasEnd": "http://www.w3.org/2006/time#hasEnd",
    "inTimePosition": "http://www.w3.org/2006/time#inTimePosition",
    "hasTRS": "http://www.w3.org/2006/time#hasTRS",
    "numericPosition": "http://www.w3.org/2006/time#numericPosition",
    "ProperInterval": "http://www.w3.org/2006/time#ProperInterval",
    "Instant": "http://www.w3.org/2006/time#Instant",
    "TimePosition": "http://www.w3.org/2006/time#TimePosition"
}

# Frame without context - uses full IRIs
FRAME_TEMPLATE = {
    "@type": "http://schema.org/Dataset",
    "@embed": "@always"
}


def is_bare_id_reference(obj):
    """Check if an object is a bare @id reference (only has @id property)"""
    if not obj or not isinstance(obj, dict):
        return False
    keys = list(obj.keys())
    return len(keys) == 1 and keys[0] == '@id'


def _is_catalog_record(item):
    """True if the item's schema:additionalType marks it as a catalog record.

    The CDIF schema:subjectOf wrapper is itself @type=schema:Dataset (so the
    Dataset frame matches it), but is distinguished by schema:additionalType
    containing 'dcat:CatalogRecord'. The main-entity picker uses this to skip
    the catalog-record entity."""
    if not isinstance(item, dict):
        return False
    at = item.get('schema:additionalType')
    if at is None:
        return False
    if isinstance(at, str):
        at = [at]
    return 'dcat:CatalogRecord' in at


def _frame_root_types(frame):
    """Return the set of compact @type tokens the frame is rooted on (e.g.
    {'schema:Dataset'} or {'skos:ConceptScheme'}). Used to pick the main entity
    from a framed @graph in a profile-agnostic way."""
    if not isinstance(frame, dict):
        return set()
    t = frame.get('@type')
    if t is None:
        return set()
    if isinstance(t, str):
        t = [t]
    out = set()
    for v in t:
        if not isinstance(v, str):
            continue
        out.add(v)
        # also keep the local name so a full-IRI frame type matches a compact one
        out.add(v.rsplit('/', 1)[-1].rsplit('#', 1)[-1])
    return out


def _type_tokens(item):
    """Set of @type tokens (and their local names) on a framed node."""
    t = item.get('@type') if isinstance(item, dict) else None
    if t is None:
        return set()
    if isinstance(t, str):
        t = [t]
    out = set()
    for v in t:
        if isinstance(v, str):
            out.add(v)
            out.add(v.rsplit('/', 1)[-1].rsplit('#', 1)[-1])
    return out


def pick_main_entity(graph, frame):
    """Choose the document's main entity from a framed @graph.

    Profile-agnostic: prefer a node whose @type matches the frame's root type
    (skipping catalog records), then a node with schema:distribution, then one
    with schema:url, then the first non-catalog-record node."""
    candidates = [it for it in graph
                  if isinstance(it, dict) and not _is_catalog_record(it)]
    if not candidates:
        return None
    # Dataset-rooted profiles: the main dataset is the one carrying a
    # distribution, then one with a url (a bare related Dataset has neither).
    for it in candidates:
        if it.get('schema:distribution') is not None:
            return it
    for it in candidates:
        if it.get('schema:url') is not None:
            return it
    # Fallback (e.g. SKOS ConceptScheme, which has neither): match the frame root.
    root_types = _frame_root_types(frame)
    if root_types:
        for it in candidates:
            if _type_tokens(it) & root_types:
                return it
    return candidates[0]


def remove_nulls_and_normalize(obj, parent_key=None):
    """
    Post-process the framed output to match schema expectations:
    1. Remove null values (framing adds null for missing optional properties)
    2. Rename unprefixed terms to prefixed versions
    3. Wrap single values in arrays where the schema expects arrays
    4. Convert bare @id references to strings for identifier fields
    """
    if isinstance(obj, list):
        # Filter out None values and process remaining items
        return [remove_nulls_and_normalize(item, parent_key) for item in obj if item is not None]

    if isinstance(obj, dict):
        result = {}

        for key, value in obj.items():
            # Skip null values
            if value is None:
                continue

            # Skip @context - pass through unchanged
            if key == '@context':
                result[key] = value
                continue

            # Rename key if needed
            new_key = TERM_MAPPINGS.get(key, key)

            # Process value recursively
            new_value = remove_nulls_and_normalize(value, parent_key=new_key)

            # Skip if value became None or empty after processing
            if new_value is None:
                continue

            # Normalize @type to array throughout the entire document
            # (framing compacts single-element arrays to strings)
            if new_key == '@type' and isinstance(new_value, str):
                new_value = [new_value]

            # Re-expand compacted cdif: IRI *values* (e.g. conformsTo profile URIs
            # like cdif:data_description/1.1) back to the full https://w3id.org/cdif/
            # form the schemas' const/contains constraints require. Framing compacts
            # these when the source document declares a cdif: prefix in its @context.
            # Only @id values are touched; cdif:-prefixed property *keys*
            # (cdif:hasPhysicalMapping, ...) are left compact as the schema expects.
            if new_key == '@id' and isinstance(new_value, str) and new_value.startswith('cdif:'):
                new_value = 'https://w3id.org/cdif/' + new_value[len('cdif:'):]

            # Convert bare @id references to strings for identifier fields
            if new_key == 'schema:identifier' and is_bare_id_reference(new_value):
                new_value = new_value['@id']

            # Wrap in array if schema expects array and value is not already an array
            if new_key in ARRAY_PROPERTIES and not isinstance(new_value, list):
                new_value = [new_value]

            result[new_key] = new_value

        # Context-aware wrapping based on @type of current node
        obj_type = result.get('@type', '')
        type_list = obj_type if isinstance(obj_type, list) else ([obj_type] if obj_type else [])

        # schema:propertyID: array inside variableMeasured and additionalProperty items,
        # string on plain Identifier PropertyValues (e.g. inside schema:identifier)
        pid_array_context = (parent_key in ('schema:variableMeasured', 'schema:additionalProperty') or
                             'cdi:InstanceVariable' in type_list)
        if pid_array_context:
            pid = result.get('schema:propertyID')
            if pid is not None and not isinstance(pid, list):
                result['schema:propertyID'] = [pid]

        # schema:measurementTechnique: array on Dataset (root), scalar inside variableMeasured
        if 'schema:Dataset' in type_list:
            mt = result.get('schema:measurementTechnique')
            if mt is not None and not isinstance(mt, list):
                result['schema:measurementTechnique'] = [mt]

        # schema:encodingFormat: array on DataDownload and on MediaObject
        # (archive member files in schema:hasPart), string on EntryPoint
        if 'schema:DataDownload' in type_list or 'schema:MediaObject' in type_list:
            ef = result.get('schema:encodingFormat')
            if ef is not None and not isinstance(ef, list):
                result['schema:encodingFormat'] = [ef]
        elif 'schema:EntryPoint' in type_list:
            ef = result.get('schema:encodingFormat')
            if isinstance(ef, list) and len(ef) == 1:
                result['schema:encodingFormat'] = ef[0]

        # schema:contributor inside Role: unwrap single-element array to bare value
        # (at root level it's an array of contributors, but inside Role it's a single agent)
        if 'schema:Role' in type_list:
            inner = result.get('schema:contributor')
            if isinstance(inner, list) and len(inner) == 1:
                result['schema:contributor'] = inner[0]

        # schema:alternateName: array on variableMeasured and spatialCoverage items,
        # string on Person/Organization
        is_var_or_place = ('cdi:InstanceVariable' in type_list or
                           'schema:PropertyValue' in type_list and parent_key == 'schema:variableMeasured' or
                           'schema:Place' in type_list)
        alt = result.get('schema:alternateName')
        if alt is not None:
            if is_var_or_place and not isinstance(alt, list):
                result['schema:alternateName'] = [alt]

        return result

    return obj


def frame_cdif_document(doc_path, frame_path=None):
    """Frame a CDIF JSON-LD document using the three-step expand/frame/compact approach."""
    print(f"Loading document: {doc_path}")
    with open(doc_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    # Load custom frame if provided, otherwise use minimal frame template
    if frame_path:
        print(f"Loading frame: {frame_path}")
        with open(frame_path, 'r', encoding='utf-8') as f:
            frame = json.load(f)
    else:
        frame = FRAME_TEMPLATE

    # Merge contexts bidirectionally so both expansion and compaction work with
    # all prefixes from either source:
    # 1. Frame prefixes -> document context: prefixed terms in the document
    #    expand to full IRIs even if the document's own context is incomplete.
    # 2. Document prefixes -> frame context: domain-specific prefixes (ada:, xas:,
    #    skos:, ...) compact correctly without requiring every prefix in the frame.
    if frame_path and isinstance(frame, dict) and '@context' in frame:
        doc_ctx = doc.get('@context', {})
        if isinstance(doc_ctx, dict):
            frame_ctx = frame['@context']
            for k, v in frame_ctx.items():
                if isinstance(v, str) and k not in doc_ctx:
                    doc_ctx[k] = v
            doc['@context'] = doc_ctx
            for k, v in doc_ctx.items():
                if isinstance(v, str) and k not in frame_ctx:
                    frame_ctx[k] = v

    # Step 1: Expand the document (resolves all prefixes to full IRIs)
    print("Expanding document...")
    expanded = jsonld.expand(doc)

    # Step 2: Frame the document
    print("Framing document...")
    framed = jsonld.frame(expanded, frame)

    # Step 3: Compact with our desired output context (if using template frame)
    if not frame_path:
        print("Compacting with output context...")
        framed = jsonld.compact(framed, OUTPUT_CONTEXT)

    # Step 4: Extract the main entity from @graph if present
    result = framed
    if '@graph' in framed and isinstance(framed['@graph'], list):
        entity = pick_main_entity(framed['@graph'], frame)
        if entity:
            result = {'@context': framed.get('@context'), **entity}

    # Step 5: Post-process to remove nulls, normalize terms and array properties
    print("Post-processing output...")
    result = remove_nulls_and_normalize(result)

    return result


def _auto_default(patterns, label):
    """Return the single file in SCRIPT_DIR matching any of the glob patterns,
    or None if there is not exactly one (caller then requires an explicit arg)."""
    hits = []
    seen = set()
    for pat in patterns:
        for p in sorted(SCRIPT_DIR.glob(pat)):
            if p.name not in seen:
                seen.add(p.name)
                hits.append(p)
    if len(hits) == 1:
        return str(hits[0])
    return None


def _load_detect_conformance():
    """Best-effort import of detect_conformance + apply_conformance from the CDIF
    validation repo. The release-repo copies of this script do not ship those
    modules, so this returns (None, None) there and --conformance becomes a no-op.
    Looks beside the script, one and two levels up (tools/ -> validation/), the
    CDIF_VALIDATION_DIR env var, and finally PYTHONPATH."""
    import os
    cands = []
    env = os.environ.get('CDIF_VALIDATION_DIR')
    if env:
        cands.append(Path(env))
    cands += [SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent]
    for c in cands:
        if c and (c / 'detect_conformance.py').is_file():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            break
    try:
        from detect_conformance import detect_conformance, apply_conformance
        return detect_conformance, apply_conformance
    except Exception:
        return None, None


def detect_and_apply_conformance(framed):
    """Detect the CDIF profiles the framed document conforms to (from its content)
    and rewrite schema:subjectOf/dcterms:conformsTo to declare them, preserving any
    non-CDIF (domain) profile claims. Returns the list of detected URIs, or None if
    detect_conformance is unavailable."""
    detect_fn, apply_fn = _load_detect_conformance()
    if detect_fn is None:
        return None
    uris = detect_fn(framed)
    apply_fn(framed, uris)
    return uris


def validate_against_schema(framed, schema_path):
    """Validate framed document against JSON Schema"""
    print(f"Loading schema: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # Use Draft 2020-12 validator
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(framed))

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def main():
    parser = argparse.ArgumentParser(
        description='CDIF JSON-LD Framing and Validation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Frame and print output (schema/frame auto-detected from this directory)
  python FrameAndValidate.py my-metadata.jsonld

  # Frame with explicit frame and save output
  python FrameAndValidate.py my-metadata.jsonld --frame cdifCore-frame.jsonld -o framed.json

  # Validate against an explicit schema
  python FrameAndValidate.py my-metadata.jsonld -v --schema cdifCoreStructuredSchema.json
"""
    )
    parser.add_argument('input', help='Input JSON-LD file to process')
    parser.add_argument('-o', '--output', help='Write framed output to file')
    parser.add_argument('-v', '--validate', action='store_true', help='Validate against JSON Schema')
    parser.add_argument('--schema', default=None,
                        help='Path to JSON Schema (default: the single *Schema*.json beside this script)')
    parser.add_argument('--frame', default=None,
                        help='Path to JSON-LD frame (default: the single *-frame.jsonld beside this script)')
    parser.add_argument('--conformance', action='store_true',
                        help='detect which CDIF profiles the framed document conforms to '
                             '(from its content) and rewrite schema:subjectOf/dcterms:conformsTo '
                             'to declare them (requires detect_conformance.py from the validation repo)')

    args = parser.parse_args()

    # Resolve auto-detected defaults when not given explicitly.
    schema_path = args.schema or _auto_default(['*Schema*.json', '*schema*.json'], 'schema')
    frame_path = args.frame or _auto_default(['*-frame.jsonld', '*frame*.jsonld'], 'frame')

    try:
        framed = frame_cdif_document(args.input, frame_path)

        if args.conformance:
            uris = detect_and_apply_conformance(framed)
            if uris is None:
                print("\n--conformance: detect_conformance.py not found (or rdflib "
                      "missing); leaving conformsTo unchanged.", file=sys.stderr)
            else:
                print("\nDetected CDIF conformance (written to schema:subjectOf/dcterms:conformsTo):")
                for u in uris:
                    print(f"  {u}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(framed, f, indent=2)
            print(f"Framed output written to: {args.output}")
        elif not args.validate:
            print("\nFramed output:")
            print(json.dumps(framed, indent=2))

        if args.validate:
            if not schema_path:
                print("Error: no schema given and could not auto-detect a single "
                      "*Schema*.json beside this script; pass --schema.", file=sys.stderr)
                sys.exit(2)
            print("\nValidating against schema...")
            result = validate_against_schema(framed, schema_path)

            if result['valid']:
                print("Validation PASSED")
            else:
                print("Validation FAILED")
                print("\nErrors:")
                for error in result['errors']:
                    path = '/'.join(str(p) for p in error.absolute_path) if error.absolute_path else '/'
                    print(f"  - /{path}: {error.message}")
                sys.exit(1)

        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

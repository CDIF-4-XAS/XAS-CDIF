#!/usr/bin/env python3
# >>> CDIF-SYNC GENERATED >>>
# GENERATED FILE -- DO NOT EDIT.
# Synced from CDIF/validation/tools/FrameAndValidate.py (the normative source).
# Edit there, then run:  python tools/sync_frameandvalidate.py --apply
# src-sha256: 96557dd2e8920337b2ca0d5853e550ec49f34d0708c5ecadaea020e6d4b7967e
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
    # An activity commonly uses several instruments in one role, so the
    # profiles pin prov:used's schema:instrument wrapper to an array.
    # Framing collapses a one-instrument list back to a bare object and
    # the document then fails a schema it actually satisfies -- every
    # XAS release example failed this way while being correct on disk.
    'schema:instrument',
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
    # cdif: was missing entirely, so every cdif:-namespaced property came out
    # of compaction as a full IRI -- 19 of them on a data-structure document.
    "cdif": "https://w3id.org/cdif/",
    "csvw": "http://www.w3.org/ns/csvw#",
    "ada": "https://ada.astromat.org/metadata/",
    # xas: is a CDIF sub-namespace, not an Astromat one. mBB binds it to
    # w3id (23 context.jsonld + 41 examples agree); this used to say
    # https://ada.astromat.org/metadata/xas/, which denotes something else.
    # Compaction prefers the longest match, so xas: still wins over cdif:.
    "xas": "https://w3id.org/cdif/xas/",
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


# --- Bare-DataStructure normalizations -------------------------------------
# These run ONLY on documents rooted directly on a DDI-CDI data-structure type
# (the cdi:has_DataStructureComponent grammar), never on Dataset / manifest /
# data-description docs, where the same keys are typed differently (e.g.
# cdi:qualifies is an array here but a single object in cdifDataDescription).
STRUCTURE_ROOT_TYPES = frozenset({
    'DataStructure', 'DimensionalDataStructure',
    'LongDataStructure', 'WideDataStructure',
})

# Keys whose value is an id-reference to another node, never an inline copy of
# it. Framing with @embed:@always inlines the whole target; these get collapsed
# back to a bare {@id} because the full node is retained at its own slot (or is
# an external resource) and the tightened schemas type these slots as {@id}-only
# references. The collapse runs on EVERY doc type (see remove_nulls_and_normalize),
# not just bare-structure docs -- cdi:qualifies also appears in dataset-rooted
# data-description docs, and schema:about (manifest part -> documented file) /
# schema:result (activity -> produced entity) are reference slots on manifest /
# provenance / dataset docs.
#
# A key belongs here ONLY when its target node is defined elsewhere in the
# document, so dropping the framing-embedded copy back to a bare {@id} is
# non-lossy. (prov:wasDerivedFrom is deliberately NOT here: in the examples its
# target is defined nowhere else, so a labelled {@id, schema:name} there is an
# authoring error -- fix the example to a bare {@id} or a full Reference with
# @type + schema:url -- not something the harness should silently collapse.)
REFERENCE_ONLY_KEYS = (
    'cdi:qualifies', 'cdi:refersTo',
    'schema:about', 'schema:result',
    # On an InstanceVariable this is an objectReference -- @id and nothing
    # else -- because the represented-variable-level properties are defined
    # once on the RepresentedVariable and deliberately not duplicated. The
    # RV node itself is reached through the data structure's components, so
    # collapsing the framing-embedded copy is non-lossy. (The same key on
    # cdifDataStructureComponent may legitimately be inline; that node is not
    # framed through this path.)
    'cdif:isDefinedBy_RepresentedVariable',
)

# Keys the (bare-structure) schema requires as arrays but framing collapses to a
# scalar / single object when there is exactly one value.
STRUCTURE_ARRAY_KEYS = ('cdif:name', 'cdi:qualifies', 'cdi:semantic')


def _collapse_to_id_ref(value):
    """Reduce an embedded node (a dict carrying @id plus other keys) to a bare
    {@id} reference. Recurses into lists; leaves inline objects without @id (e.g.
    an anonymous role) and plain strings untouched."""
    if isinstance(value, list):
        return [_collapse_to_id_ref(v) for v in value]
    if isinstance(value, dict) and '@id' in value and len(value) > 1:
        return {'@id': value['@id']}
    return value


def _is_structure_rooted(doc):
    """True if the raw document's top-level @type names a DDI-CDI data structure."""
    if not isinstance(doc, dict):
        return False
    t = doc.get('@type')
    if isinstance(t, str):
        t = [t]
    if not isinstance(t, list):
        return False
    return any(_local_name(v) in STRUCTURE_ROOT_TYPES for v in t)


def normalize_bare_structure(obj):
    """Recursive normalizations for bare DataStructure documents: collapse
    framing-inlined component references (cdi:qualifies / cdi:refersTo) back to
    bare {@id}, and wrap single-valued STRUCTURE_ARRAY_KEYS into arrays."""
    if isinstance(obj, list):
        return [normalize_bare_structure(x) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            v = normalize_bare_structure(v)
            if k in REFERENCE_ONLY_KEYS:
                v = _collapse_to_id_ref(v)
            if k in STRUCTURE_ARRAY_KEYS and not isinstance(v, list):
                v = [v]
            out[k] = v
        return out
    return obj


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


def _referenced_ids(graph):
    """@ids that appear *inside* some node -- i.e. that something points at.

    Framing hoists any node matching the frame's root type to the top of
    @graph, so a dataset's parts land beside the dataset itself when they
    are Datasets too. The one nothing else points at is the document's
    subject; the rest are its children.
    """
    refs = set()

    def walk(node, owner):
        if isinstance(node, dict):
            got = node.get('@id')
            if isinstance(got, str) and got != owner:
                refs.add(got)
            for key, value in node.items():
                if key != '@id':
                    walk(value, owner)
        elif isinstance(node, list):
            for value in node:
                walk(value, owner)

    for item in graph:
        if isinstance(item, dict):
            owner = item.get('@id')
            walk({k: v for k, v in item.items() if k != '@id'}, owner)
    return refs


def pick_main_entity(graph, frame):
    """Choose the document's main entity from a framed @graph.

    Profile-agnostic: prefer a node nothing else references (the root of a
    hasPart tree), then one whose @type matches the frame's root type
    (skipping catalog records), then a node with schema:distribution, then one
    with schema:url, then the first non-catalog-record node.

    The unreferenced-node check has to come FIRST. Without it, a dataset
    whose parts carry the distributions -- a package of independently
    accessible resources, where the aggregate itself has no single
    download -- loses to its own first part on the schema:distribution
    test, and the validator then reports on the part while silently
    discarding the dataset. Every such record passes, because the thing
    being checked was never the thing being described.
    """
    candidates = [it for it in graph
                  if isinstance(it, dict) and not _is_catalog_record(it)]
    if len(candidates) > 1:
        referenced = _referenced_ids(graph)
        roots = [it for it in candidates
                 if it.get('@id') not in referenced]
        if roots:
            candidates = roots
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


def _content_signature(x):
    """Canonical JSON of x with blank-node @ids (_:bN) normalized away, so two
    nodes that differ only by their framing-assigned blank-node identifier compare
    equal. Non-blank @ids are kept, so genuinely distinct references never match."""
    def norm(v):
        if isinstance(v, dict):
            return {k: (None if k == '@id' and isinstance(val, str) and val.startswith('_:')
                        else norm(val))
                    for k, val in sorted(v.items())}
        if isinstance(v, list):
            return [norm(i) for i in v]
        return v
    return json.dumps(norm(x), sort_keys=True, ensure_ascii=False)


def _dedupe_framing_dupes(items):
    """Drop later dict items whose content signature (ignoring blank-node @ids)
    duplicates an earlier one -- an @embed:@always framing artifact where the same
    node is emitted more than once with distinct _:bN ids (e.g. a schema:identifier
    duplicated on a publisher). Scalars and distinct nodes are left untouched."""
    seen = set()
    out = []
    for item in items:
        if isinstance(item, dict):
            sig = _content_signature(item)
            if sig in seen:
                continue
            seen.add(sig)
        out.append(item)
    return out


def remove_nulls_and_normalize(obj, parent_key=None):
    """
    Post-process the framed output to match schema expectations:
    1. Remove null values (framing adds null for missing optional properties)
    2. Rename unprefixed terms to prefixed versions
    3. Wrap single values in arrays where the schema expects arrays
    4. Convert bare @id references to strings for identifier fields
    5. Drop framing-produced duplicate nodes (same content, distinct blank @ids)
    """
    if isinstance(obj, list):
        # Filter out None values, process remaining items, then drop framing dupes
        items = [remove_nulls_and_normalize(item, parent_key) for item in obj if item is not None]
        return _dedupe_framing_dupes(items)

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

            # Collapse framing-embedded references back to a bare {@id} for
            # reference-only slots (the tightened schemas type these as {@id};
            # framing with @embed:@always inlines the whole target). Ungated --
            # runs on every doc type, before the array wrap below.
            if new_key in REFERENCE_ONLY_KEYS:
                new_value = _collapse_to_id_ref(new_value)

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

        # schema:about: array on manifest archive/part nodes (a part pointing at
        # the part it documents), but a single {@id} inside a schema:subjectOf
        # catalog record (the back-reference to the described resource). Framing
        # embeds the referenced node and collapses the single-item array, so wrap
        # it back -- except inside schema:subjectOf, where the schema types it as
        # a single object. Keyed on parent_key (not the catalog-record marker,
        # whose schema:additionalType form varies: 'dcat:CatalogRecord' vs
        # {'@id': 'dcat:CatalogRecord'}).
        # ...and not on a DefinedTerm. The XAS profile identifies the absorption
        # edge and target element with a keywords `contains` whose schema:about
        # is a const STRING ("element.edge" / "element.symbol"); wrapping it made
        # every XAS record miss both, so the profile's two defining terms went
        # unrecognised. No CDIF schema wants an array here -- the ones that do
        # (profile-manifest's hasPart items, CDIF-graph's MediaObject) are never
        # DefinedTerms.
        if parent_key != 'schema:subjectOf' and 'schema:DefinedTerm' not in type_list:
            about = result.get('schema:about')
            if about is not None and not isinstance(about, list):
                result['schema:about'] = [about]

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

        # schema:identifier: single object/string on Person/Organization agents
        # (the schema types it anyOf[Identifier, string], not an array). Framing --
        # especially after deduping a framing-duplicated identifier node -- can
        # leave a single-element array; unwrap it to match the agent schema.
        if 'schema:Organization' in type_list or 'schema:Person' in type_list:
            ident = result.get('schema:identifier')
            if isinstance(ident, list) and len(ident) == 1:
                result['schema:identifier'] = ident[0]

        # ...but an array on an instrument, where the schema pins
        # schema:instrument/items/properties/schema:identifier to type: array
        # ("Formal identifier(s)" -- a device can carry a PID, a serial number
        # and an inventory number at once). schema:identifier cannot go in
        # ARRAY_PROPERTIES, which is keyed on name alone, because the agent case
        # directly above needs the opposite; so key off the parent property.
        # Sub-parts in schema:hasPart are anyOf, not array, and parent_key is
        # 'schema:hasPart' there, so this correctly leaves them alone.
        if parent_key == 'schema:instrument':
            ident = result.get('schema:identifier')
            if ident is not None and not isinstance(ident, list):
                result['schema:identifier'] = [ident]

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

    # Step 6: For bare DataStructure documents only, apply structure-specific
    # normalizations (reference collapse + array wrapping) that must NOT run on
    # Dataset / manifest / data-description docs (same keys, different types).
    if _is_structure_rooted(doc):
        result = normalize_bare_structure(result)

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


FRAME_PATTERNS = ['*-frame.jsonld', '*frame*.jsonld']


def _local_name(token):
    """Local name of a type token: strip after the last '/', '#' or ':'.
    'schema:Dataset' -> 'Dataset'; 'cdi:WideDataStructure' -> 'WideDataStructure';
    'http://schema.org/Dataset' -> 'Dataset'. Lets a compact frame root match a
    full-IRI document root and vice versa."""
    if not isinstance(token, str):
        return None
    for sep in ('/', '#', ':'):
        token = token.rsplit(sep, 1)[-1]
    return token


def _root_type_names(json_path):
    """Set of local @type names on a JSON(-LD) file's top-level node."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        return set()
    t = d.get('@type') if isinstance(d, dict) else None
    if t is None:
        return set()
    if isinstance(t, str):
        t = [t]
    return {n for n in (_local_name(v) for v in t) if n}


def _auto_frames():
    """All frame files beside this script (deduped, sorted)."""
    hits, seen = [], set()
    for pat in FRAME_PATTERNS:
        for p in sorted(SCRIPT_DIR.glob(pat)):
            if p.name not in seen:
                seen.add(p.name)
                hits.append(p)
    return hits


def _select_frame(input_path):
    """Pick the frame beside this script for the given input document.

    Zero frames -> None (caller falls back to the minimal Dataset template).
    One frame  -> that frame (unchanged single-frame behaviour, no matching).
    Many frames -> the frame whose root @type best matches the document's root
    @type (by local name). A profile can thus ship a second, differently-rooted
    frame (e.g. a bare-structure frame alongside the Dataset frame) and have the
    right one chosen per input. If no frame's root matches, return None so the
    Dataset template default applies."""
    frames = _auto_frames()
    if not frames:
        return None
    if len(frames) == 1:
        return str(frames[0])
    doc_roots = _root_type_names(input_path)
    best, best_score = None, 0
    for fr in frames:
        score = len(doc_roots & _root_type_names(fr))
        if score > best_score:
            best, best_score = fr, score
    return str(best) if best is not None else None


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
    # A release-repo copy sits at its repo root, with the validation repo
    # checked out as a sibling, so look for CDIF/validation/ from one and two
    # levels up as well. Without this the check silently no-ops in exactly the
    # repos whose examples it is meant to check.
    cands += [SCRIPT_DIR.parent / 'validation',
              SCRIPT_DIR.parent.parent / 'validation']
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


def detect_and_apply_conformance(framed, source_doc=None):
    """Detect the CDIF profiles the record conforms to (from its content) and
    rewrite schema:subjectOf/dcterms:conformsTo on `framed` to declare them,
    preserving any non-CDIF (domain) profile claims. Returns the list of detected
    URIs, or None if detect_conformance is unavailable.

    Detection reads `source_doc` -- the document as authored -- not the framed
    result. Framing drops evidence below schema:distribution, so detecting from
    it omits profiles the record genuinely satisfies (data_structure is the one
    that bites), and this function PERSISTS its answer: a narrowed conformsTo
    would be written into the output file. The rewrite still targets `framed`,
    since that is what gets serialized."""
    detect_fn, apply_fn = _load_detect_conformance()
    if detect_fn is None:
        return None
    uris = detect_fn(source_doc if source_doc is not None else framed)
    apply_fn(framed, uris)
    return uris


# Mirrors detect_conformance.CDIF_BASE: the profile space CDIF manages. Claims
# outside it (a project or domain profile) are the record's own business, and
# apply_conformance preserves them, so they are never reported as inconsistent.
CDIF_URI_PREFIX = "https://w3id.org/cdif/"


def _declared_conformance(doc):
    """The dcterms:conformsTo URIs the record declares on schema:subjectOf.

    Tolerates subjectOf being a dict or a list, and each conformsTo entry being
    either {"@id": uri} or a plain string."""
    subj = doc.get("schema:subjectOf")
    if isinstance(subj, dict):
        subj = [subj]
    if not isinstance(subj, list):
        return set()
    out = set()
    for s in subj:
        if not isinstance(s, dict):
            continue
        claims = s.get("dcterms:conformsTo")
        if isinstance(claims, (dict, str)):
            claims = [claims]
        for entry in (claims or []):
            if isinstance(entry, dict):
                entry = entry.get("@id")
            if isinstance(entry, str):
                out.add(entry)
    return out


def check_conformance_consistency(framed, source_doc=None):
    """Compare what the record CLAIMS to conform to against what its content
    actually supports, per detect_conformance.

    Returns None when detect_conformance is unavailable -- the release-repo
    copies of this script do not ship it, so the check degrades to a no-op
    there rather than failing.

    Both halves are read from `source_doc` (the document as authored) when one
    is given. Framing is lossy in both directions: it can drop schema:subjectOf
    outright, so the declaration would read as "declares nothing"; and evidence
    below schema:distribution does not survive it, so detection under-reports
    and a correct record looks like it is over-claiming."""
    detect_fn, _ = _load_detect_conformance()
    if detect_fn is None:
        return None
    # Only profiles the registry can actually produce are comparable. Declaring
    # one it has no rule for (codelist, complexCitation, ...) would otherwise
    # look like an over-claim every single time.
    try:
        from detect_conformance import CONFORMANCE_CLASSES
        detectable = {c["uri"] for c in CONFORMANCE_CLASSES}
    except Exception:
        detectable = None
    subject = source_doc if source_doc is not None else framed
    detected = {u for u in (detect_fn(subject) or [])
                if u.startswith(CDIF_URI_PREFIX)}
    declared_all = _declared_conformance(subject)
    declared = {u for u in declared_all if u.startswith(CDIF_URI_PREFIX)}
    comparable = declared if detectable is None else (declared & detectable)
    return {
        'declared': sorted(declared),
        'detected': sorted(detected),
        'overclaimed': sorted(comparable - detected),
        'undeclared': sorted(detected - declared),
        'other': sorted(declared_all - declared),
        'unchecked': sorted(declared - comparable),
        'lost_in_framing': bool(declared and not _declared_conformance(framed)),
    }


def report_conformance_consistency(report):
    """Print the declared-vs-detected comparison. Returns True when they agree."""
    print()
    print("Checking declared conformsTo against detected conformance...")
    if report['lost_in_framing']:
        print("  NOTE: the source declares conformsTo but framing dropped "
              "schema:subjectOf, so the declaration was read from the source "
              "document. The framed output declares nothing.")
    if not report['declared'] and not report['detected']:
        print("  No CDIF conformsTo declared and none detected.")
    for uri in report['overclaimed']:
        print("  DECLARED BUT NOT DETECTED: %s" % uri)
    for uri in report['undeclared']:
        print("  DETECTED BUT NOT DECLARED: %s" % uri)
    for uri in report.get('unchecked') or []:
        print("  not checked (no detection rule): %s" % uri)
    for uri in report['other']:
        print("  (outside the CDIF profile space, not checked: %s)" % uri)
    agree = not report['overclaimed'] and not report['undeclared']
    if agree and report['declared']:
        n = len(report['declared']) - len(report.get('unchecked') or [])
        print("  Conformance CONSISTENT: %d declared CDIF profile(s) match the "
              "detected conformance." % n)
    elif report['overclaimed']:
        print("  Conformance FAILED: %d over-claimed profile(s) - declared but "
              "not supported by the content" % len(report['overclaimed']))
    else:
        print("  Conformance INCONSISTENT (under-claimed only; advisory)")
    return agree


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
    overclaimed = []

    # Resolve auto-detected defaults when not given explicitly.
    schema_path = args.schema or _auto_default(['*Schema*.json', '*schema*.json'], 'schema')
    frame_path = args.frame or _select_frame(args.input)

    try:
        framed = frame_cdif_document(args.input, frame_path)

        # The document as authored. Both the --conformance rewrite and the -v
        # consistency check read conformance from this rather than from `framed`,
        # because framing is lossy.
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                source_doc = json.load(f)
        except Exception:
            source_doc = None

        if args.conformance:
            uris = detect_and_apply_conformance(framed, source_doc)
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
            # Among the validation tests: does the record's declared
            # conformsTo agree with what its content actually supports?
            # Skipped after --conformance, which has just rewritten the
            # declaration to the detected set, making agreement trivial.
            if not args.conformance:
                report = check_conformance_consistency(framed, source_doc)
                if report is None:
                    print("\nConformance check skipped: detect_conformance.py "
                          "not found (or rdflib missing).")
                else:
                    report_conformance_consistency(report)
                    overclaimed = report['overclaimed']

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

            # Deferred to here so a schema failure reports its errors first
            # rather than being masked by the conformance exit.
            if overclaimed:
                print("\nFAILED: conformsTo declares %d profile(s) the content "
                      "does not support:" % len(overclaimed))
                for uri in overclaimed:
                    print("  %s" % uri)
                sys.exit(1)

        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

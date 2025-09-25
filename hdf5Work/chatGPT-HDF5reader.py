import h5py
import json
import numpy as np


def classify_datasets(h5file):
    """
    Classify datasets in an HDF5 file into measures, dimensions, and attributes (context datasets).
    """

    classification = {"measures": [], "dimensions": [], "attributes": []}
    datasets_info = {}

    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset):
            info = {
                "path": name,
                "shape": obj.shape,
                "dtype": str(obj.dtype),
                "attrs": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in obj.attrs.items()},
                "dims": [d.label for d in obj.dims if hasattr(d, "label")],
            }
            datasets_info[name] = info

    h5file.visititems(visitor)

    # Identify dimensions from dimension scales or naming
    dim_candidates = set()
    for name, info in datasets_info.items():
        try:
            if len(info["shape"]) == 1:
                # 1D arrays are strong dimension candidates
                dim_candidates.add(name)
            # Check if attached as a dimension scale
            for d in info["dims"]:
                if d and d != "":  # dimension label present
                    dim_candidates.add(name)
        except:
            print(name, info["shape"], info["dims"])

    # Classify datasets
    for name, info in datasets_info.items():
        print("name, shape", name, info["shape"])
        try:
            if name in dim_candidates:
                # If numeric or datetime-ish, call it a dimension
                if np.issubdtype(np.dtype(info["dtype"]), np.number) or "time" in name.lower():
                    classification["dimensions"].append(info)
                else:
                    classification["attributes"].append(info)
            else:
                # If matches shape of dimension sets, call it a measure
                if any(len(info["shape"]) > 0 and dim_len in info["shape"]
                       for dim_len in [datasets_info[d]["shape"][0] for d in dim_candidates if datasets_info[d]["shape"]]):
                    classification["measures"].append(info)
                else:
                    classification["attributes"].append(info)
        except Exception as e:
            print(name, info["shape"], info["dims"])

    return classification


def build_jsonld(classification, dataset_name="HDF5 Dataset"):
    """
    Build a JSON-LD structure from classified datasets.
    """
    jsonld = {
        "@context": {
            "@vocab": "https://schema.org/",
            "ddi": "https://ddi-alliance.org/ns/cdi#"
        },
        "@type": "Dataset",
        "name": dataset_name,
        "variableMeasured": []
    }

    def checkForBytes(inval):
        if isinstance(inval, np.bytes_):
            return inval.decode("utf-8", errors="replace")
    def add_var(info, role):
        jsonld["variableMeasured"].append({
            "@type": "PropertyValue",
            "name": info["path"].split("/")[-1],
            "dataset": "/" + info["path"],
            "encodingFormat": "application/x-hdf5",
            "ddi:role": role,
            "additionalProperty": [
                {"@type": "PropertyValue", "name": checkForBytes(k), "value": checkForBytes(v)}
                for k, v in info["attrs"].items()
            ]
        })

    for info in classification["measures"]:
        add_var(info, "Measure")
    for info in classification["dimensions"]:
        add_var(info, "Dimension")
    for info in classification["attributes"]:
        add_var(info, "Attribute")

    return jsonld


if __name__ == "__main__":
    dir = "C:/Users/smrTu/OneDrive/Documents/GithubC/CDIF/exampledata/"
    #dir = "C:/Users/smrTu/OneDrive/Documents/GithubC/CDIF/exampledata/IPNS/LRMECS/hdf4/"
    #filename="lrcs3701.nxs"
    filename = "Soleil/hdf5/file_1.nxs"
    hdf5_path = dir + filename
    # path to your HDF5 file
    with h5py.File(hdf5_path, "r") as f:
        classification = classify_datasets(f)

    jsonld_doc = build_jsonld(classification, dataset_name="Example HDF5 Dataset")

    # Save JSON-LD
    with open("hdf5_metadata.jsonld", "w") as out:
        json.dump(jsonld_doc, out, indent=2)

    print(json.dumps(jsonld_doc, indent=2))

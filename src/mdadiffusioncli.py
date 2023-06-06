import yaml
import mdadiffusion
import numpy as np
import os

import argparse


def numpy_to_arrays(d):
    def denumpy(x):
        if isinstance(x, np.ndarray) or isinstance(x, np.float_):
            return x.tolist()
        elif isinstance(x, dict):
            return denumpy(x)
        else:
            return x

    return {denumpy(k): denumpy(v) for k, v in d.items()}


def round_floats(d):
    def rf(x):
        if isinstance(x, float):
            return round(x, 4)
        elif isinstance(x, dict):
            return round_floats(x)
        else:
            return x

    return {k: rf(v) for k, v in d.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimum Dissipation approximation.")
    parser.add_argument(
        "--config",
        metavar="c.yaml",
        type=str,
        help="Global config (densities, sizes, etc)",
        required=True,
    )
    parser.add_argument(
        "--proteins",
        metavar="p.yaml",
        type=str,
        nargs="+",
        help="Config yamls for each protein (sequecnes, names)",
        required=True,
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Directory for output",
        required=True,
    )

    args = parser.parse_args()

    print(args)

    with open(args.config) as in_file:
        global_config = yaml.safe_load(in_file)
        print(global_config)

    for protein in args.proteins:
        with open(protein) as in_file:
            protein_config = yaml.safe_load(in_file)
            print(protein_config)

        bead_model = mdadiffusion.mda.bead_model_from_sequence(
            annotated_sequence=protein_config["AnnotatedSequence"],
            effective_density=global_config["OrderedBeads"]["EffectiveDensity"],
            hydration_thickness=global_config["OrderedBeads"]["HydrationThickness"],
            disordered_radii=global_config["DisorderedBeads"]["HydrodynamicRadius"],
            c_alpha_distance=global_config["DisorderedBeads"]["CAlphaDistance"],
            aa_masses=global_config["AminoAcidMasses"],
        )

        rh_dict = mdadiffusion.mda.hydrodynamic_size(
            bead_steric_radii=bead_model["steric_radii"],
            bead_hydrodynamic_radii=bead_model["hydrodynamic_radii"],
            ensemble_size=100,
            bootstrap_rounds=20,
        )

        computation_result = dict()

        computation_result["HydrodynamicRadius_MDA"] = rh_dict["rh_mda"]
        computation_result["HydrodynamicRadius_MDA_error"] = rh_dict["rh_mda (se)"]
        computation_result["HydrodynamicRadius_Kirkwood"] = rh_dict["rh_kr"]
        computation_result["HydrodynamicRadius_Kirkwood_error"] = rh_dict["rh_kr (se)"]

        computation_result["ProteinName"] = protein_config["ProteinName"]
        computation_result["AnnotatedSequence"] = protein_config["AnnotatedSequence"]

        print(yaml.dump(round_floats(numpy_to_arrays(computation_result))))

        with open(args.output + os.path.basename(protein), "w") as out_file:
            out_file.write(yaml.dump(round_floats(numpy_to_arrays(computation_result))))

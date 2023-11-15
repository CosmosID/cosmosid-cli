from enum import Enum


AMPLICON_PRESETS = {
    "v1_v3": {
        "forward_primer": "AGAGTTTGATCCTGGCTCAG",
        "reverse_primer": "ATTACCGCGGCTGCTGG",
    },
    "v3_v4": {
        "forward_primer": "CCTACGGGRSGCAGCA",
        "reverse_primer": "GACTACHVGGGTATCTAATCC",
    },
    "v4": {
        "forward_primer": "GTGYCAGCMGCCGCGGTAA",
        "reverse_primer": "GGACTACHVGGGTWTCTAAT",
    },
}

HOST_REMOVAL_OPTIONS = {
    "human:2.0.0": "Human 2.0.0 (GCF_009914755.1_T2T-CHM13v2.0)",
    "human:1.0.0": "Human 1.0.0 (GRCh38_p6)",
    "dog:2.0.0": "Dog (GCF_014441545.1_ROS_Cfam_1.0)",
    "domestic_cat:2.0.0": "Domestic Cat (GCF_018350175.1_F.catus_Fca126_mat1.0)",
    "cow:1.0.0": "Cow (GCF_002263795l_1_ARS-UCD1_2)",
    "chicken:2.0.0": "Chicken (GCF_016699485.2_bGalGal1.mat.broiler.GRCg7b)",
    "mouse:2.0.0": "Mouse (GCF_000001635.27_GRCm39)",
    "monkey:2.0.0": "Monkey (GCF_003339765.1_Mmul_10)",
    "cattle:2.0.0": "Cattle (GCF002263795.2 - ARS-UCD1.3)",
    "pig:2.0.0": "Pig (GCF_000003025.6_Sscrofa11.1)",
}

FILE_TYPES = {"metagenomics": 2, "amplicon-16s": 5, "amplicon-its": 6}


class Workflows:
    BatchImport = "120b2c3e-4c3b-4fcd-9f56-db507005dcb2"
    AmpliseqBatchGroup = "53aeffd2-f33d-4774-a3a3-1caa2765bd9a"


class ComparativeExportType(Enum):
    matrix = "matrix-table"
    alpha_diversity = "alpha-diversity"
    beta_diversity = "beta-diversity"
    read_statistics = "read-statistics"
    multiqc = "multiqc-zip"
    ampliseq_summary = "ampliseq-summary"
    lefse = "lefse"


class TaxonomicRank(Enum):
    kingdom = "kingdom"
    order = "order"
    phylum = "phylum"
    class_ = "class"
    family = "family"
    genus = "genus"
    species = "species"
    strain = "strain"

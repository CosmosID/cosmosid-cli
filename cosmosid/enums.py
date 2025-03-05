from enum import Enum


PROGRAM_NAME = "cosmosid"

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

SAMPLE_TYPES = {
    "2": "Shotgun metagenomics (WGS)",
    "5": "Amplicon 16S",
    "6": "Amplicon ITS",
}

WF_DESCRIPTION = {
    (
        "amplicon_its",
        "1.0.0",
    ): """Amplicon ITS workflow allows you to characterize the fungi in a microbial community based on ITS
(internal transcribed spacer) region with a genus to species taxonomic resolution of fungi.""",
    (
        "amplicon_16s",
        "1.0.0",
    ): """Amplicon 16S workflow allows you to characterize the bacteria in a microbial community based on 16S rRNA
marker gene with a genus to species taxonomic resolution of bacteria.""",
    (
        "ampliseq",
        "1.0.0",
    ): """Amplicon 16S workflow allows you to characterize the bacteria in a microbial community based on 16S rRNA
marker gene with a genus to species taxonomic resolution of bacteria.""",
    (
        "ampliseq_batch",
        "1.0.0",
    ): """Amplicon 16S workflow allows you to characterize the bacteria in a microbial community based on 16S
rRNA marker gene with a genus to species taxonomic resolution of bacteria.

Please be advised, we recommend running Amplicon 16S workflow with a batch of sequencing data that has
been generated from the same sequencing run. Running the Amplicon 16S workflow in a group of samples
from the same sequencing run allows for more accurate error correction and denoising because it takes
advantage of the technical variability present within the sequencing run. This variability can be used
to identify and correct errors that are specific to the sequencing run, rather than errors that are
specific to individual samples. That&#39;s why running Amplicon 16S with only 1 sample may not yield
successful results.""",
    (
        "ampliseq_batch_group",
        "1.0.0",
    ): """Amplicon 16S workflow allows you to characterize the bacteria in a microbial community based on 16S
rRNA marker gene with a genus to species taxonomic resolution of bacteria.

Please be advised, we recommend running Amplicon 16S workflow with a batch of sequencing data that has
been generated from the same sequencing run. Running the Amplicon 16S workflow in a group of samples
from the same sequencing run allows for more accurate error correction and denoising because it takes
advantage of the technical variability present within the sequencing run. This variability can be used
to identify and correct errors that are specific to the sequencing run, rather than errors that are
specific to individual samples. That&#39;s why running Amplicon 16S with only 1 sample may not yield
successful results.""",
    (
        "amr_vir",
        "1.0.0",
    ): """The AMR and Virulence Marker workflow allows you to characterize the antimicrobial and virulence genes
in the microbiome community.""",
    (
        "functional",
        "1.0.0",
    ): """The Functional workflow allows you to leverage the power of the MetaCyc Pathway and Gene Ontology
databases to characterize and predict the functional potential of the underlying microbiome community.

If you are planning to run Functional 1.0 workflow for your data, please consider running Functional
2.0 since Functional 1.0 will be phased out and will be unavailable on the HUB in 6 months time.""",
    (
        "functional2",
        "1.0.0",
    ): """The Functional workflow 2.0 allows you to leverage the power of the Enzyme Commission, Pfam, CAZy,
MetaCyc Pathway and Gene Ontology databases to characterize and predict the functional potential of
the underlying microbiome community.
        
If you haven’t chosen the sample specimen host in Step 2, please go back to Step 2 and select the
respective host for your dataset. We recommend running Functional 2.0 with Host Read Depletion step.
The only exception to this recommendation is environmental samples.""",
    (
        "taxa",
        "1.0.0",
    ): """The Taxa workflow allows you to leverage the power of the CosmosID taxonomic databases to characterize
the microbiome community with strain level resolution across multiple kingdoms.""",
    (
        "taxa",
        "1.1.0",
    ): """The Taxa workflow allows you to leverage the power of the CosmosID taxonomic databases to characterize
the microbiome community with strain level resolution across multiple kingdoms.""",
    (
        "taxa",
        "1.2.0",
    ): """The Taxa workflow allows you to leverage the power of the CosmosID taxonomic databases to characterize
the microbiome community with strain level resolution across multiple kingdoms.""",
    (
        "bacteria_beta",
        "1.0.0",
    ): """The Bacteria Beta 2.1.0 workflow allows you to characterize the composition of the bacterial community
in your sample with our new Bacterial Beta Database 2.1.0.""",
    (
        "kepler",
        "1.0.0",
    ): '''We are delighted to present the newest edition of our Taxa Workflow, "Taxa-Kepler". The taxa
      workflow has been upgraded to effectively merge the sensitivity and precision of our k-mer methodology
      with our novel Probabilistic Smith-Waterman read-alignment approach. The resulting integration not only
      augments the ability to estimate taxa abundance but also enhances the classification accuracy and
      precision. Experience accurate microbiome community characterization with "Taxa-Kepler"''',
    (
        "champ_taxa",
        "1.0.0",
    ): """CHAMP is designed specifically for human-derived samples, utilizing over 400,000 metagenome-assembled
genomes (MAGs), created from a collection of more than 30,000 microbiome samples across 9 different body sites from individuals across the world.
This workflow produces multi-kingdom taxonomic profiles.""",
    (
        "champ_functional_kegg_module",
        "1.0.0",
    ): """CHAMP is designed specifically for human-derived samples, utilizing over 400,000 metagenome-assembled
genomes (MAGs), created from a collection of more than 30,000 microbiome samples across 9 different body sites from individuals across the world.
This workflow provides KEGG Orthologs and KEGG Modules functional abundances based on species whose genomes contain these two given modules.""",
    (
        "champ_functional_gbm_gmm",
        "1.0.0",
    ): """CHAMP is designed specifically for human-derived samples, utilizing over 400,000 metagenome-assembled
genomes (MAGs), created from a collection of more than 30,000 microbiome samples across 9 different body sites from individuals across the world.
This workflow provides both Gut-Metabolic Modules (GMM) and Gut-Brain Modules (GBM) functional abundances based on species whose genomes contain these two given modules.""",
    (
        "champ_taxa_functional_gbm_gmm",
        "1.0.0",
    ): """CHAMP is designed specifically for human-derived samples, utilizing over 400,000 metagenome-assembled
genomes (MAGs), created from a collection of more than 30,000 microbiome samples across 9 different body sites. This workflow produces multi-kingdom taxonomic profiles
as well as functional characterization based on Gut-Metabolic Modules (GMM) and Gut-Brain Modules (GBM).""",
    (
        "champ_taxa_functional_gbm_gmm_kegg_module",
        "1.0.0",
    ): """CHAMP is designed specifically for human-derived samples, utilizing over 400,000 metagenome-assembled
genomes (MAGs), created from a collection of more than 30,000 microbiome samples across 9 different body sites. This workflow produces multi-kingdom taxonomic profiles
as well as functional characterization based on Gut-Metabolic Modules (GMM), Gut-Brain Modules (GBM), and KEGG database.""",
    (
        "unilever_bacterial",
        "1.0.0",
    ): """The 16S rRNA workflow classifies genus- and species-level taxonomy based on Amplicon Sequence Variants
determined by the DADA2 algorithm using GreenGenes2 and HOMD database.""",
    (
        "unilever_bacterial_homd",
        "1.0.0",
    ): """The 16S rRNA workflow classifies genus- and species-level taxonomy based on Amplicon Sequence Variants
determined by the DADA2 algorithm using HOMD database.""",
    (
        "unilever_bacterial_greengenes2",
        "1.0.0",
    ): """The 16S rRNA workflow classifies genus- and species-level taxonomy based on Amplicon Sequence Variants
determined by the DADA2 algorithm using GreenGenes2 database.""",
}

CLI_NAME_TO_WF_NAME = {"ampliseq": "ampliseq_batch_group"}

WF_NAME_TO_CLI_NAME = {value: key for key, value in CLI_NAME_TO_WF_NAME.items()}

HIDDEN_WFS = [
    "ampliseq",
]


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

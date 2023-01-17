from enum import Enum


class ComparativeExportType(Enum):
    matrix = 'matrix-table'
    alpha_diversity = 'alpha-diversity'
    beta_diversity = 'beta-diversity'
    read_statistics = 'read-statistics'
    multiqc = 'multiqc-zip'


class TaxonomicRank(Enum):
    kingdom = 'kingdom'
    order = 'order'
    phylum = 'phylum'
    class_ = 'class'
    family = 'family'
    genus = 'genus'
    species = 'species'
    strain = 'strain'

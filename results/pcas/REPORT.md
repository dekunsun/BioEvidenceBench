# PCAS botany external case (exploratory)

Eastwood 1898, PCAS 3rd ser. Botany vol. 1, 8 pages (BHL item 48989). Gold by Gloria against the scans (210 rows as labelled; 206 after her adjudication, made after model outputs were seen). Value-level (bag) F1, all pages pooled (8 pages: no interval). Opus 5.5. Not comparable with the main experiment's positional scores, and not pooled with it.

| field       |   ('adjudicated', 'G1F · pcas_legacy') |   ('adjudicated', 'G2 · pcas_legacy') |   ('adjudicated', 'V1 · image') |   ('as labelled', 'G1F · pcas_legacy') |   ('as labelled', 'G2 · pcas_legacy') |   ('as labelled', 'V1 · image') |
|:------------|---------------------------------------:|--------------------------------------:|--------------------------------:|---------------------------------------:|--------------------------------------:|--------------------------------:|
| ALL_PRIMARY |                                  0.803 |                                 0.938 |                           0.94  |                                  0.703 |                                 0.831 |                           0.833 |
| taxon       |                                  0.725 |                                 0.961 |                           0.99  |                                  0.725 |                                 0.961 |                           0.99  |
| person      |                                  0.606 |                                 0.843 |                           0.824 |                                  0.323 |                                 0.569 |                           0.549 |
| locality    |                                  0.973 |                                 0.987 |                           0.987 |                                  0.928 |                                 0.928 |                           0.928 |
| institution |                                  1     |                                 1     |                           1     |                                  0.769 |                                 0.769 |                           0.769 |
| date        |                                  0.667 |                                 0.667 |                           0.667 |                                  0.667 |                                 0.667 |                           0.667 |
| vernacular  |                                  0.696 |                                 0.809 |                           0.84  |                                  0.696 |                                 0.809 |                           0.84  |

| gold_version   | condition         |   tp |   fp |   fn |     P |     R |    F1 |
|:---------------|:------------------|-----:|-----:|-----:|------:|------:|------:|
| as labelled    | G1F · pcas_legacy |  130 |   58 |   52 | 0.691 | 0.714 | 0.703 |
| as labelled    | G2 · pcas_legacy  |  155 |   36 |   27 | 0.812 | 0.852 | 0.831 |
| as labelled    | V1 · image        |  155 |   35 |   27 | 0.816 | 0.852 | 0.833 |
| adjudicated    | G1F · pcas_legacy |  147 |   41 |   31 | 0.782 | 0.826 | 0.803 |
| adjudicated    | G2 · pcas_legacy  |  173 |   18 |    5 | 0.906 | 0.972 | 0.938 |
| adjudicated    | V1 · image        |  173 |   17 |    5 | 0.911 | 0.972 | 0.94  |

Misses and extra outputs per condition: `misses.csv`.

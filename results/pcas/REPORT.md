# PCAS botany external case (exploratory)

Eastwood 1898, PCAS 3rd ser. Botany vol. 1, 8 pages (BHL item 48989). Gold by Gloria against the scans (210 rows). Value-level (bag) F1, all pages pooled (8 pages: no interval). Opus 5.5. Not comparable with the main experiment's positional scores, and not pooled with it.

| field       |   gold |   G1F · pcas_legacy |   G2 · pcas_legacy |   V1 · image |
|:------------|-------:|--------------------:|-------------------:|-------------:|
| ALL_PRIMARY |    182 |               0.703 |              0.831 |        0.833 |
| taxon       |     50 |               0.725 |              0.961 |        0.99  |
| person      |     46 |               0.323 |              0.569 |        0.549 |
| locality    |     77 |               0.928 |              0.928 |        0.928 |
| institution |      7 |               0.769 |              0.769 |        0.769 |
| date        |      2 |               0.667 |              0.667 |        0.667 |
| vernacular  |     28 |               0.696 |              0.809 |        0.84  |

| condition         |   tp |   fp |   fn |     P |     R |    F1 |
|:------------------|-----:|-----:|-----:|------:|------:|------:|
| G1F · pcas_legacy |  130 |   58 |   52 | 0.691 | 0.714 | 0.703 |
| G2 · pcas_legacy  |  155 |   36 |   27 | 0.812 | 0.852 | 0.831 |
| V1 · image        |  155 |   35 |   27 | 0.816 | 0.852 | 0.833 |

Misses and extra outputs per condition: `misses.csv`.

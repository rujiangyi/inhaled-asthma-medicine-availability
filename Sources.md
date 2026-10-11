# Data provenance and reuse

Prepared 5 October 2026 for local research and submission preparation. These archives combine third-party data and derived research results. No blanket open licence is assigned to either archive or to its contents, and no public repository deposit has been performed. Packaging the files locally does not establish permission for unrestricted redistribution. Dataset-specific conditions and any agreement accepted by the downloader continue to govern reuse; authors should verify those conditions before public deposition. No statement of permission or source-organisation endorsement is inferred.

## WHO

The source is the WHO Noncommunicable Disease Country Capacity Survey as served by the Global Health Observatory API. The retained national waves are 2013, 2015, 2017, 2019 and 2021. Primary analyses use 2017/2019/2021; original question text for 2013/2015 was not verified. Medicine endpoints include:

- https://ghoapi.azureedge.net/api/NCD_CCS_Steroid
- https://ghoapi.azureedge.net/api/NCD_CCS_Bronchodilators
- https://ghoapi.azureedge.net/api/NCD_CCS_ComboInhaler

The three endpoints provide reported general availability, not verified patient access or clinical treatment. Unknown answers are retained. The 2021 combination item is not retrospectively treated as No. The local field metadata and questionnaire audit retain the public-primary-care setting and the pharmacy availability threshold. Source attribution: World Health Organization, NCD Country Capacity Survey / Global Health Observatory, indicator and wave as recorded, audit checked 5 October 2026.

The official [WHO dataset terms](https://data.who.int/about/data/terms-and-conditions) describe licensing, attribution and third-party exceptions for data.who.int. The files here were obtained from GHO endpoints; this package does not silently assume that a general platform statement settles every source-specific condition. Source metadata should accompany any permitted redistribution.

## World Bank

World Development Indicators were obtained through API v2 for 2017–2021. Indicator codes are EN.ATM.PM25.MC.M3, NY.GDP.PCAP.PP.KD, SH.XPD.OOPC.CH.ZS and SH.XPD.CHEX.PP.CD. Query form: https://api.worldbank.org/v2/country/all/indicator/{indicator}?date=2017:2021&format=json&source=2 . The API responses and country metadata are retained in the code archive. The harmonised extraction frame contains 181 countries, not all 194 WHO records. COK and NIU are unmatched to the retained World Bank country metadata; thirteen WHO countries were outside extraction.

Attribution: World Bank, World Development Indicators, indicator-specific source and units as retained in the metadata. Consult the [dataset summary terms](https://data.worldbank.org/summary-terms-of-use) and [World Bank permissions page](https://www.worldbank.org/en/about/legal/permissions), including attribution and any third-party dataset conditions. The archive does not replace these with a newly invented licence.

## IHME / Global Burden of Disease

Source: Institute for Health Metrics and Evaluation (IHME), Global Burden of Disease Study 2023 Results. The retained local exports were downloaded on 14 September 2026 and reduced to asthma DALYs and resident population for both sexes aged 25 years or older, 2010–2021. The analysis uses 2021 for the main burden shares. Results tool: https://vizhub.healthdata.org/gbd-results/ . The population and DALY exports are matched by GBD location and year. Release provenance is supported by internal export citations, download namespace and hashes. The original export citation lists 2024; the dataset publication year has not been independently confirmed. Dataset releases and methods articles are different bibliographic objects: the methods articles' publication in 2025 does not establish that the dataset date is incorrect. The original citation and download receipts are preserved. The dynamic results tool is cited as undated, accessed 5 October 2026; the frozen exports were downloaded on 14 September 2026. Temporary job links later returned 404. Full original download ZIPs are not included; the retained reduced inputs support offline replay.

The official [IHME non-commercial agreement](https://www.healthdata.org/sites/default/files/files/free-of-charge_non-commercial_user_agreement.pdf) distinguishes research/publication results from redistribution of source datasets and contains restrictions. The archive is not an assertion that the individual downloader has permission to redistribute every included extract publicly. Confirm the applicable accepted agreement and any required source acknowledgment before external deposition. The phrase “used with permission” is not added without evidence. Derived tables and figure source data still retain IHME-derived numerical values; their location in the data archive does not make them unrestricted public-domain data.

## Natural Earth and fonts

Natural Earth 1:10m Admin 0 Countries, version 5.1.1, provides display geometry only. Source: https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/ . Its [terms page](https://www.naturalearthdata.com/about/terms-of-use/) identifies Natural Earth map data as public domain. The code archive retains the fixed source and simplified geometry with provenance. These are not official WHO/IHME statistical boundaries and are not used to aggregate exposure or population.

Times New Roman font files are not redistributed. Exact figure rendering requires an appropriately licensed installation visible to Matplotlib. Missing fonts may prevent the plotting scripts from running; numerical tables do not require the font. No reference-paper PDF, reference figure image or third-party executable is included.

## Scope of validation

The contents are national aggregate records, not patient-level data. No means below the reporting threshold, not zero medicine supply. Population counts are residents, not untreated patients. The estimates are exploratory; no joint GBD uncertainty draws are included and no causal treatment effect is implied. Source correctness, source reuse permissions and the scientific assumptions are distinct from numerical replay and archive CRC checks.

# Data dictionary

The archive has 68 analytical/source CSVs: 19 under Statistics, 43 under Figures and six under Additional. Inventory.json gives each filename, source, exact row count, column names and SHA256 hash. CSVs are UTF-8 (most include a byte-order mark). Numeric blank cells denote unavailable values, not zero. Existing source field names are preserved to keep the frozen CSVs byte-identical; the no-underscore naming convention applies to filenames and directories, not to original field identifiers.

## Country data.csv

| Field | Meaning |
|---|---|
| iso3 | Retained country identifier used for linkage; identifiers do not certify identical territorial support across sources. |
| country | Source country/territory label. |
| region | WHO region code: AFR, AMR, EMR, EUR, SEAR or WPR. |
| balanced168 | True for valid ICS and bronchodilator Yes/No in every primary wave. |
| ics2017, ics2019, ics2021 | Original national steroid-inhaler answer for the stated wave; item not explicitly single-agent. |
| bronch2021 | Original national bronchodilator-inhaler answer in 2021; not verified salbutamol-specific. |
| combo2021 | Original national budesonide–formoterol answer in 2021. |
| trajectory | Chronological 2017/2019/2021 ICS Y/N sequence where all three ICS responses are valid. Main trajectory analyses additionally require balanced168. |
| daly2021 | GBD 2023 asthma DALY number, calendar year 2021, both sexes aged 25 years or older. |
| rate2021 | Crude asthma DALY rate per 100,000 residents aged 25 years or older; not age-standardised. |
| pop2021 | GBD resident population aged 25 years or older; not number of patients. |
| pm25 | National annual mean population-weighted ambient PM2.5, µg/m³, exact 2021. |
| gdp | GDP per capita PPP, constant 2021 international dollars, exact 2021. |
| oop | Out-of-pocket health expenditure as percent of current health expenditure, exact 2021. |
| health | Current health expenditure per capita PPP, current international dollars, exact 2021. |
| geo_review | Historical cartographic/territorial-scope flag; not proof of a failed country ID. |

The current environmental extraction is limited to 181 countries. Values absent outside that frame do not establish source-level WDI missingness. COK/NIU did not match the retained World Bank country metadata; item missingness among matched countries is a separate category.

## WHO responses.csv

Year identifies the survey wave, not an established retrospective medication reference window. Country code, Country, WHO region code and WHO region retain source identifiers and labels. The Chinese fields 吸入激素, 支气管扩张剂 and 复方吸入剂 mean ICS, bronchodilator and budesonide–formoterol, respectively. 肺量计, 峰流速, 呼吸病计划 and 呼吸病指南 denote spirometry, peak flow, respiratory-disease plan and guideline items retained for provenance; they were not used as covariates in the reported models. Both medicines valid refers to explicit Yes/No for ICS and bronchodilator; Medicine state is their derived joint state.

Yes and No are reported general-availability categories. No means below the survey threshold, not no medicine supply. Do not know, no response, no data received and no observation for year remain distinct source labels. The early combination field has structural absence, not a historical No. Raw codes and wording are retained in the code archive's source metadata. The ≥50% threshold concerns pharmacies in the public-primary-care medication context; it must not be relabelled as a percentage of all facilities or patients.

## Model estimates.csv and Model diagnostics.csv

model_id identifies a fixed specification; family/model_role record primary, economic-replacement or sensitivity roles. outcome identifies the national 2021 ICS or combination answer, coded No=1 and Yes=0. eligible_n precedes complete-case exclusions; complete_n is the fitted or checked sample; events_no and nonevents_yes are the two outcome counts. variable is gdp, health, pm25 or oop, with the increment explicitly recorded in unit. log_odds_coefficient and robust_se are on the log-odds scale; odds_ratio and ci95_lower/upper are exponentiated coefficient and HC1 Wald limits. p_wald_exploratory is an exploratory two-sided Wald P value, without multiple-model correction. covariance records independent-country HC1 with n/(n−p).

GDP/health use log2 (per doubling); PM2.5 is per 10 µg/m³; OOP is per 10 percentage points. GDP and health never enter together. Common-sample suffixes identify equal country sets, not merely equal sample sizes. The diagnostic file retains included_iso3, excluded_missing_iso3, excluded_missing_n, status, stop_reason, separation_check, convergence, warnings and numerical conditioning. The one not_fitted row has no invented coefficient. Blank fit diagnostics on a stopped row mean estimation was not reached. HC1 does not correct cross-country dependence, source error or spatial correlation.

## Statistical tables and figure source files

All statistical CSVs are described individually in Inventory.json. Names containing count/n are counts of countries unless explicitly a DALY or population variable. Country percentages use the denominator field in that row; *_percent_global204 uses all 204 GBD country/territory units. DALYs and resident population are age 25+; crude-rate variables use per 100,000. Paired yes_yes/yes_no/no_yes/no_no read earlier response first and later response second. change_percentage_points is later minus earlier Yes percentage. p_exact_mcnemar uses discordant pairs, and p_holm_within_medicine_three_comparisons corrects three comparisons within medicine/sample.

Figure filenames identify the source figure and panel. Source rows include plotted observed values and deterministic summaries; coordinates used solely for display are not additional observations. Labels such as DALY share and population share are percentages within the retained sample. Omitted ISO3 identifies the removed country; retained countries is the recalculated denominator count. NNN indicates No in all three primary waves. Cumulative omissions follow the fixed initial rank, whereas the individual-country omission file removes one country at a time. Neither is a bootstrap sample or confidence interval.

For missing scenario bounds, bound_type distinguishes wave general availability, trajectory compatibility and combination unknown assignments. lower/upper counts or percentages are deterministic extremes. Trajectory upper bounds are marginal and cannot be added across sequences. The all-WHO denominator194 and primary-panel denominator168 answer different questions. Unknowns are unchanged in the original data and never recoded into the fitted models. Joint GBD uncertainty draws were not available; marginal lower/upper endpoints were not summed to create joint intervals.

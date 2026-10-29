# Research and quantitative analysis handoff

Research finds and verifies source evidence. Analysis evaluates structured inputs, calculations and uncertainty. Choose analysis when a conclusion depends on KPI definitions, sales/conversion, period comparisons, cohorts, forecasts, scenarios or survey data. Simple arithmetic can use a transparent local calculation; larger or uncertain models use actually available specialist Data Analytics workflows. A plugin name is not tool readiness.

| Analytical need | Appropriate specialist, if available | Required evidence |
|---|---|---|
| KPI/measurement framework | `design-kpis` | Definitions, population, denominator, source, cadence, owner; proposed targets remain proposals |
| Performance readout | `kpi-reporting` | Comparable periods, actual versus target, missingness and measurement method |
| Why a metric changed | `metric-diagnostics` | Validated baseline/segments, data-quality checks; association versus supported causality |
| Missing/duplicate/outdated structured data | `analyze-data-quality` | Grain, schema, joins, nulls, freshness and exclusions |
| Forecast, cohort, scenario, survey or reproducible model | `jupyter-notebooks` / `product-business-analysis` | Reproducible transformations, assumptions, uncertainty and constraints |
| Independent calculation/method audit | `validate-data` | Input authority, formula, units, comparison and conclusion support |

Scope the specialist request as analysis support when the employee's requested final artifact is a DEMO document. Read and follow the actual invoked skill's current contract. A requested analytical dashboard/report has its own durable-output workflow; do not invoke that workflow as an incidental calculation then leave its requirements unfinished. Do not publish a dashboard merely because analysis tools are present. Retain the employee's requested final file and existing authorization; additional external data transmission, installation or paid execution needs its actual consent scope.

## One traceable result

Use the existing evidence record with an `analysis_id` and affected claim IDs. Include only needed fields: input paths/source IDs and hashes; period, grain, units and population; formula or reproducible model path; exclusions and assumptions; result/uncertainty; validation scope; affected section/chart IDs. Store a compact result table in the project when needed, not a duplicate research database.

The analyst returns checked results, limitations, changed inputs and affected dependents. Writing preserves actual/forecast/target distinctions. Design uses supported values and truthful scales; charts register input dependencies under [project state](project-state.md). A newer CSV invalidates an older chart and its exported document even when the HTML filename is unchanged. Research still verifies external authority/currentness; a correct calculation cannot certify its inputs as current facts.

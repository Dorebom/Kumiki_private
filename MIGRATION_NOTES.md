# CI Consolidation Notes

This package contains the consolidated GitHub Actions workflows based on the agreed plan:

- Keep **kumiki_ci_publish_plus.yml** as the main PR/Push pipeline (Lint → Trace → IDCheck → Reach → Gate → Build; Pages is split into prepare/upload and deploy jobs).
- Add **i18n_check** and **impact_analysis** jobs inside the main workflow.
- Keep **docops_ann_swap.yml** as a slim, specialized PR/workflow_dispatch benchmark for ANN connectors (no Pages, no DocOps duplicate steps).
- Add **docops_search_eval.yml** for nightly Search Evaluation via schedule.

Removed/merged (delete from your repo if present):
- docops_min.yml
- docops_i18n.yml
- docops_impact.yml
- docops_trace.yml
- docops_secscan.yml
- docops_gen_index.yml
- docops_search.yml
- docops_reach.yml
- kumiki_ci_publish.yml

Tips:
- If you want i18n or impact to gate PRs, remove the `|| true` from their scripts so non-zero exit codes fail the job.
- Adjust cron in `docops_search_eval.yml` as needed.
- Ensure required scripts exist under `tools/docops_cli` or `tools/ci` before enabling strict gating.

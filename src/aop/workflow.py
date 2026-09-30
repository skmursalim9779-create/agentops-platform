WORKFLOW = """\
name: agent-eval-gate
on:
  pull_request:
  workflow_dispatch:
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install .
      - name: Run eval gate
        run: |
          if [ -f .aop/baseline/results.json ]; then
            aop eval run --baseline .aop/baseline/results.json
          else
            aop eval run
          fi
      - name: Publish report
        if: always()
        run: cat .aop/results/latest/report.md >> "$GITHUB_STEP_SUMMARY"
      - uses: actions/upload-artifact@v4
        if: always()
        with: {name: eval-results, path: .aop/results/latest/}
"""

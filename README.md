# voyagekit

Process AIS-style vessel position logs: parse position fixes, compute the distance each vessel travelled, and flag implausible speeds between fixes.

```
python -m voyagekit summary --synthetic 20000
python -m voyagekit alerts --file positions.log
```

Install Python 3.12 or newer, then install the development dependencies:

```sh
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Benchmarks

The harness uses `pytest-codspeed` with the `benchmark` fixture. CPU simulation
is appropriate for the parsing, grouping, sorting, and geodesic computations.
There are 18 benchmark cases in `tests/benchmarks/test_core_benchmarks.py`:

| Operation | Inputs |
| --- | --- |
| Parse a log | 1,000 and 20,000 fixes; ordered, shuffled, and single-vessel logs |
| Group and sort by vessel | The same four scenarios |
| Calculate track distances | The same four scenarios |
| Detect speed alerts | The same four scenarios |
| Parse and summarize / parse and detect alerts | Two pipelines, each with 20,000 fixes and 50 vessels |

Inputs use fixed random seeds, include position jumps, and are prepared outside
the measured calls. Parsing also covers comments and blank lines. Each case
checks its output outside measurement. The pipelines measure the application
computations together; file/network I/O, input generation, and console output
are excluded. Individual haversine calls are covered by the distance and alert
workloads rather than timing a tiny standalone call.

Run correctness checks without performance measurement (also works on Windows):

```sh
python -m pytest tests/benchmarks -q
```

On a supported Linux host, install and authenticate the
[CodSpeed CLI](https://codspeed.io/docs/cli), activate the virtual environment,
then run:

```sh
codspeed auth login
codspeed run -m simulation -- python -m pytest tests/benchmarks --codspeed
```

Expect 18 benchmarks, performance results, and a report link. Check the report
for flamegraphs. A successful ordinary pytest run verifies correctness only;
it does not establish that CodSpeed instrumentation or upload works. The
CodSpeed CLI does not support native Windows. `pytest-codspeed` can execute
benchmark bodies there, but its Windows build has no native measurement hooks.

`.github/workflows/codspeed.yml` runs correctness checks and CPU simulation on
Ubuntu for pushes to `main`, pull requests, and manual dispatch. Enable
`Lemuel-micro1/lho-codspeed-fx02` in the CodSpeed GitHub integration before
expecting reports. The workflow uses CodSpeed's OIDC authentication permissions.
A root `codspeed.yml` is unnecessary for this language-specific harness: the
CLI and action invoke pytest directly.

See `docs/benchmark-setup-log.txt` for the setup evidence, tool-call log, and
verification limitations.

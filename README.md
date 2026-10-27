# TestEm3DEDX

**Electron dE/dX validated by actually tracking particles** through a thin
absorber (multiple scattering and energy-loss fluctuations left on), as a
cross-check of [`TestDEDX2`](https://github.com/G4Med-test/TestDEDX2), which
computes the same quantity analytically with `G4EmCalculator` and never
transports a single particle. Built on the `TestEm3` sampling-calorimeter
example.

[![CI Pipeline](https://github.com/G4Med-test/TestEm3DEDX/actions/workflows/ci.yml/badge.svg)](https://github.com/G4Med-test/TestEm3DEDX/actions/workflows/ci.yml)

---

## 🔬 What this test does

A mono-energetic e- beam hits a single thin G4_WATER absorber (one layer, one
material), with multiple scattering and Landau/Vavilov energy-loss
fluctuations left **on** (unlike `TestEm3`'s own `dedx.mac`, which turns both
off to get a clean, deterministic value from the tracking-verbose output): a
genuine test of the real stepping/tracking machinery, not just the physics
tables it queries. `Run::EndOfRun` prints the mean energy deposited per event
and its RMS for that absorber; dividing the mean by the absorber's areal
density (thickness × density) gives a mass stopping power directly
comparable to `TestDEDX2` and NIST ESTAR (MeV cm2/g).

The production cut is set to a 1 km range (`/run/setCut 1 km`), suppressing
explicit delta-ray and bremsstrahlung secondaries so their energy is folded
into the continuous loss deposited in-step. Without it, this was checked
locally to read low by an amount that **grows with beam energy** — escaping
secondaries carry an increasing share of the energy out of the thin slab:
about 4% at 3 MeV, 17% at 10 MeV, 34% at 30 MeV. With the cut, the tracked
value agrees with the NIST reference to 2.3%, 0.15% and 0.27% respectively.
That reference is NIST ESTAR data for water, computed in C++ with the same
`G4ESTARStopping` class `TestDEDX2` uses (never a value typed from memory)
and printed by the application itself alongside the tracked measurement.

## 🛠️ Fill in the repository (from the template)

| Path | What it contains |
| --- | --- |
| `main.cc`, `src/`, `include/` | The Geant4 application, imported from `geant-validation-tests/src/TestEm3`. Two changes from the original: `HistoManager.hh` included the removed `g4root.hh` header (fixed to `G4AnalysisManager.hh`, caught by actually compiling against Geant4 11.3.2); `Run::EndOfRun` gained the NIST ESTAR reference printout described below. |
| `macro/unit.mac` | One-event smoke test (water, `emstandard_opt0`). |
| `macro/e-_G4_WATER_emstandard_opt0.mac` | Scans 3/10/30 MeV through a 0.15 cm water slab. |
| `validation/config.json` | Lists that one macro. |
| `validation/parser.py` | Reads the `sumX`/`sumX2` and `ESTAR_DEDX` lines `Run::EndOfRun` prints to stdout and exports both dE/dX curves (tracked and NIST reference) vs. beam energy. |

See [`validation/README.md`](validation/README.md) for exactly how the parser
reads the output and the production-cut rationale above.

## 🚀 How to run the container

```bash
apptainer build --build-arg PROJECT_NAME=TestEm3DEDX TestEm3DEDX.sif Apptainer.def
apptainer run TestEm3DEDX.sif macro/e-_G4_WATER_emstandard_opt0.mac
```

No Geant4 datasets are needed for this test, but the shared container still
mounts `/g4data` as usual.

See the top-level [template README](https://github.com/G4Med-test/template#readme)
for the full local workflow (pulling the CI-built container and running
`ci-workflows/validation/export.py`).

## 📦 Container on GHCR

[![Container on GHCR](https://img.shields.io/badge/Container-GHCR-blue?logo=github)](https://github.com/orgs/G4Med-test/packages?repo_name=TestEm3DEDX)

```bash
apptainer pull oras://ghcr.io/g4med-test/testem3dedx:<tag>
```
> Replace `<tag>` with the desired release tag or commit hash.

## ✅ GitHub Actions workflow

Defined in the shared [`ci-workflows`](https://github.com/G4Med-test/ci-workflows)
repository and invoked from [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

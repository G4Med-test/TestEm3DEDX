# Portal JSON parser

New parser (no `geant-config-generator` precedent): `TestEm3DEDX` reuses the
`geant-validation-tests/src/TestEm3` application as a thin-absorber dE/dX
measurement, to validate `TestDEDX2`'s `G4EmCalculator`-based dE/dX against a
real simulation that tracks particles through matter with multiple scattering
and energy-loss fluctuations left on (unlike `TestEm3`'s own `dedx.mac`, which
turns both off to read a clean, deterministic value off the tracking verbose
output).

The one macro keeps a single thin G4_WATER absorber
(`/testem/det/setNbOfAbsor 1`, `/testem/det/setAbsor 1 G4_WATER 0.15 cm`) and
scans three beam energies (3, 10, 30 MeV) with one `/run/beamOn` each.
`Run::EndOfRun` (edited for this repository; everything else in `src/`/
`include/` is an unmodified copy) prints, once per run:

- `... sumX: <raw sum of per-event energy deposit, MeV> sumX2: <raw sum of
  squares> ...` — full double precision, more reliable to parse than the
  `G4BestUnit`-formatted columns on the same line;
- `ESTAR_DEDX: <energy MeV> <material> <dE/dX, MeV cm2/g>` — the NIST ESTAR
  reference for the same energy and material, computed in C++ with
  `G4ESTARStopping`, the same class `TestDEDX2` uses. This keeps the
  reference curve real NIST data read from Geant4's own dataset, never a
  value typed into the Python parser from memory.

`parse()` recomputes the mean and its standard error from `sumX`/`sumX2` and
the known event count, divides by the absorber's areal density (thickness ×
`DENSITIES["G4_WATER"]` in `parser.py`) to get a mass stopping power in
MeV cm2/g, and reads the `ESTAR_DEDX` lines for the reference curve — both
under the observable name `dE/dX`, as in `TestDEDX2`, so the portal can
overlay this test's tracked curve, `TestDEDX2`'s analytic curve, and the
NIST reference.

**Why `/run/setCut 1 km`:** a thin slab's *energy deposit* is not the same
thing as the particle's *stopping power* once delta rays and bremsstrahlung
photons are explicitly produced and can escape the slab before depositing
their own energy — and the fraction that escapes grows with beam energy.
Checked locally against the ESTAR value before adding the cut: the tracked
dE/dX read low by about 4% at 3 MeV, 17% at 10 MeV, and 34% at 30 MeV. Setting
the production cut to a range of 1 km (as `TestDEDX2`'s own "cut1km" column
does) suppresses explicit secondaries below an energy far above anything
these beams produce, folding their energy into the continuous loss deposited
in-step; with it, the three energies agree with ESTAR to 2.3%, 0.15% and
0.27%. `metadata()` requires `/run/setCut 1 km` for exactly this reason.

**Verified by actually building and running the application** (not just read):
against a local Geant4 11.3.2 install, with `CMAKE_PREFIX_PATH` pointing at it
and at a Qt5 install (this Geant4 build needs Qt5Core to configure even
without visualization requested). This caught a real portability bug in the
copied `HistoManager.hh` — `#include "g4root.hh"`, a header removed from
modern Geant4 — fixed by switching to `G4AnalysisManager.hh`, which every
other file in this application already used. `unit.mac` and the validation
macro both ran correctly after the fix, in well under a second for the full
60000-event scan.

The pipeline uploads `validation-json/results.json` (an array of plot objects)
and `plots/*.json` (the original one-object-per-file format), plus raw artifacts.
See [ci-workflows](https://github.com/G4Med-test/ci-workflows) for local CLI usage.

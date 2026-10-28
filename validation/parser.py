#!/usr/bin/env python

# TestEm3DEDX portal parser: metadata() reads the macro, parse() the per-run
# "sumX"/"sumX2" and "ESTAR_DEDX" lines Run::EndOfRun prints to stdout for the
# single G4_WATER absorber. Unlike TestDEDX2 (which calls G4EmCalculator and
# G4ESTARStopping directly, with no particle transport at all), this
# application tracks real e- through a thin water slab with multiple
# scattering and energy-loss fluctuations left on, and derives dE/dX from the
# mean energy actually deposited: a cross-check of the tracking/stepping
# machinery itself, not just the physics tables it queries.
#
# The macro sets /run/setCut 1 km: with explicit delta-ray and bremsstrahlung
# secondaries suppressed, their energy is folded into the continuous loss
# deposited in-step, so the tracked value and the NIST ESTAR reference (also
# printed by the application itself, via the same G4ESTARStopping dataset
# TestDEDX2 uses) are the same unrestricted quantity. Without that cut, this
# was checked locally to read low by an amount that grows with beam energy
# (escaping secondaries carry an increasing fraction of the energy out of the
# thin slab): ~4% at 3 MeV, ~17% at 10 MeV, ~34% at 30 MeV.
import math
import os
import re

from geantval import energy_mev, getJSON, one_command

DENSITIES = {"G4_WATER": 1.0}  # g/cm3

SUMX_RE = re.compile(r"sumX:\s*([-+0-9.eE]+)\s*sumX2:\s*([-+0-9.eE]+)")
ESTAR_RE = re.compile(r"ESTAR_DEDX:\s*([-+0-9.eE]+)\s+(\S+)\s+([-+0-9.eE]+)")


def parse(job):
    text = open(os.path.join(job["path"], "test_stdout.txt")).read()

    sum_matches = SUMX_RE.findall(text)
    if len(sum_matches) != len(job["ENERGIES"]):
        raise ValueError("Found %d 'sumX' summaries in stdout, expected %d (one per beamOn)"
                         % (len(sum_matches), len(job["ENERGIES"])))

    tracked, tracked_err = [], []
    for (sumx_s, sumx2_s), n in zip(sum_matches, job["NEVENTS"]):
        sumx, sumx2 = float(sumx_s), float(sumx2_s)
        mean = sumx / n
        rms = math.sqrt(max(sumx2 / n - mean * mean, 0.0))
        tracked.append(mean / job["AREAL_DENSITY"])
        tracked_err.append(rms / math.sqrt(n) / job["AREAL_DENSITY"])

    estar_matches = ESTAR_RE.findall(text)
    if len(estar_matches) != len(job["ENERGIES"]):
        raise ValueError("Found %d 'ESTAR_DEDX' lines in stdout, expected %d (one per beamOn)"
                         % (len(estar_matches), len(job["ENERGIES"])))
    estar = []
    for (energy_s, material, dedx_s), expected in zip(estar_matches, job["ENERGIES"]):
        if material != job["MATERIAL"]:
            raise ValueError("ESTAR_DEDX material %s does not match the macro" % material)
        if not math.isclose(float(energy_s), expected, rel_tol=1e-6):
            raise ValueError("ESTAR_DEDX energy does not match the macro")
        estar.append(float(dedx_s))

    target = job["MATERIAL"].removeprefix("G4_")
    params = [{"names": "thickness_cm", "values": job["THICKNESS_CM"]}]

    yield getJSON(job, "chart",
                 mctool_name="GEANT4",
                 mctool_model=job["PHYSLIST"],
                 observableName="dE/dX",
                 targetName=target,
                 beamParticle="e-",
                 beamEnergies=job["ENERGIES"],
                 secondaryParticle="None",
                 title="dE/dX",
                 xAxisName="E, MeV",
                 yAxisName="dE/dX, MeV cm2/g",
                 parameters=params,
                 xValues=job["ENERGIES"],
                 yValues=tracked,
                 yStatErrorsPlus=tracked_err,
                 yStatErrorsMinus=tracked_err)

    yield getJSON(job, "chart",
                 mctool_name="NIST",
                 mctool_model="ESTAR",
                 observableName="dE/dX",
                 targetName=target,
                 beamParticle="e-",
                 beamEnergies=job["ENERGIES"],
                 secondaryParticle="None",
                 title="dE/dX",
                 xAxisName="E, MeV",
                 yAxisName="dE/dX, MeV cm2/g",
                 parameters=params,
                 xValues=job["ENERGIES"],
                 yValues=estar)


def metadata(commands):
    physlist = one_command(commands, "/testem/phys/addPhysics")

    if one_command(commands, "/testem/det/setNbOfAbsor") != "1":
        raise ValueError("This validation expects a single absorber")

    num, material, thickness, unit = one_command(commands, "/testem/det/setAbsor").split()
    if unit != "cm":
        raise ValueError("Expected the absorber thickness in cm, got " + unit)
    if material not in DENSITIES:
        raise ValueError("No reference density for material: " + material)
    thickness_cm = float(thickness)

    if one_command(commands, "/run/setCut") != "1 km":
        raise ValueError("This validation requires /run/setCut 1 km, to suppress "
                         "explicit secondaries and match the unrestricted ESTAR value")

    energies, nevents = [], []
    energy = None
    for command, value in commands:
        if command == "/gun/energy":
            energy = energy_mev(value)
        if command == "/run/beamOn":
            n = int(value)
            if energy is None or n <= 0:
                raise ValueError("Each beamOn needs an explicit energy and positive event count")
            energies.append(energy)
            nevents.append(n)
    if not energies:
        raise ValueError("No energy scan in macro")

    return {"TEST": "TestEm3DEDX",
            "PHYSLIST": physlist,
            "MATERIAL": material,
            "THICKNESS_CM": thickness_cm,
            "AREAL_DENSITY": thickness_cm * DENSITIES[material],
            "ENERGIES": energies, "NEVENTS": nevents}

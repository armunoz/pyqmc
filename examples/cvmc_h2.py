import pyqmc
import numpy as np

def setuph2(r, obdm_steps=5):
    from pyscf import gto, scf, lo
    from pyqmc.accumulators import LinearTransform, EnergyAccumulator
    from pyqmc.obdm import OBDMAccumulator
    from pyqmc.cvmc import DescriptorFromOBDM, PGradDescriptor

    import itertools

    # ccECP from A. Annaberdiyev et al. Journal of Chemical Physics 149, 134108 (2018)
    basis = {
        "H": gto.basis.parse(
            """
    H S
23.843185 0.00411490
10.212443 0.01046440
4.374164 0.02801110
1.873529 0.07588620
0.802465 0.18210620
0.343709 0.34852140
0.147217 0.37823130
0.063055 0.11642410
"""
        )
    }
    """
H S
0.040680 1.00000000
H S
0.139013 1.00000000
H P
0.166430 1.00000000
H P
0.740212 1.00000000
"""
    ecp = {
        "H": gto.basis.parse_ecp(
            """
    H nelec 0
H ul
1 21.24359508259891 1.00000000000000
3 21.24359508259891 21.24359508259891
2 21.77696655044365 -10.85192405303825
"""
        )
    }

    mol = gto.M(
        atom=f"H 0. 0. 0.; H 0. 0. {r}", unit="bohr", basis=basis, ecp=ecp, verbose=5
    )
    mf = scf.RHF(mol).run()
    mo_occ = mf.mo_coeff[:, mf.mo_occ > 0]
    a = lo.iao.iao(mol, mo_occ)
    a = lo.vec_lowdin(a, mf.get_ovlp())

    obdm_up = OBDMAccumulator(mol=mol, orb_coeff=a, nstep=obdm_steps, spin=0)
    obdm_down = OBDMAccumulator(mol=mol, orb_coeff=a, nstep=obdm_steps, spin=1)

    wf = pyqmc.slater_jastrow(mol, mf)


    freeze = {}
    for k in wf.parameters:
        freeze[k] = np.zeros(wf.parameters[k].shape,dtype='bool')
    print(freeze.keys())
    print(wf.parameters['wf1mo_coeff_alpha'])
    #this freezing allows us to easily go between bonding and 
    # AFM configurations.
    freeze['wf1mo_coeff_alpha'][0,0]=True
    freeze['wf1mo_coeff_beta'][1,0]=True


    descriptors = {
        "t": [[(1.0, (0, 1)), (1.0, (1, 0))], [(1.0, (0, 1)), (1.0, (1, 0))]],
        "trace": [[(1.0, (0, 0)), (1.0, (1, 1))], [(1.0, (0, 0)), (1.0, (1, 1))]],
    }
    for i in [0, 1]:
        descriptors[f"nup{i}"] = [[(1.0, (i, i))], []]
        descriptors[f"ndown{i}"] = [[], [(1.0, (i, i))]]

    acc = PGradDescriptor(
        EnergyAccumulator(mol),
        LinearTransform(wf.parameters, freeze=freeze),
        [obdm_up, obdm_down],
        DescriptorFromOBDM(descriptors, norm=2.0),
    )

    return {"wf": wf, "acc": acc, "mol": mol, "mf": mf, "descriptors": descriptors}



if __name__ == "__main__":
    import pyqmc
    import pyqmc.dasktools
    from pyqmc.dasktools import distvmc as vmc
    from pyqmc.dasktools import line_minimization
    from pyqmc.cvmc import optimize
    from dask.distributed import Client, LocalCluster   
    r = 1.1

    ncore = 2
    sys = setuph2(r)
    cluster = LocalCluster(n_workers=ncore, threads_per_worker=1)
    client = Client(cluster)

    # Set up calculation
    nconf = 800
    configs = pyqmc.initial_guess(sys["mol"], nconf)

    wf, dfgrad, dfline = line_minimization(
        sys["wf"],
        configs,
        pyqmc.gradient_generator(sys["mol"], sys["wf"]),
        client=client,
        maxiters=5,
    )

    forcing = {}
    obj = {}
    for k in sys["descriptors"]:
        forcing[k] = 0.0
        obj[k] = 0.0

    forcing["t"] = 0.5
    forcing["trace"] = 1.0
    obj["t"] = 0.0
    obj["trace"] = 2.0

    datafile = "saveh2.json"

    wf, df = optimize(
        sys["wf"],
        configs,
        sys["acc"],
        objective=obj,
        forcing=forcing,
        iters=50,
        tstep=0.1,
        datafile=datafile,
        vmc=vmc,
        vmcoptions=dict(client=client, nsteps=100),
    )

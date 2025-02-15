from pathlib import Path

def are_equal(path1, path2):
    return path1.exists() and path2.exists() and path1.stat().st_size == path2.stat().st_size

def make_base(path):
    return path.parent/path.name.replace("_PD.",".").replace("_HD.",".")

base_paths = set(map(make_base,Path("./src/images").glob("*.jp*")))

for base_path in base_paths:
    pd_path = base_path.parent/f"{base_path.stem}_PD.jpeg"
    hd_path = base_path.parent/f"{base_path.stem}_HD.jpeg"
    nu_path = base_path

    if pd_path.exists() and hd_path.exists() and nu_path.exists():
        if are_equal(pd_path, hd_path) and are_equal(hd_path, nu_path):
            pd_path.unlink()
            hd_path.unlink()
        if are_equal(pd_path, hd_path):
            hd_path.unlink()
            nu_path.unlink()
            pd_path.rename(pd_path.parent/pd_path.name.replace("_PD.","."))
        if not are_equal(pd_path, hd_path):
            nu_path.unlink()

    elif pd_path.exists() and hd_path.exists() and are_equal(pd_path, hd_path):
        hd_path.unlink()
        pd_path.rename(pd_path.parent/pd_path.name.replace("_PD.","."))

    elif pd_path.exists() and nu_path.exists():
        if are_equal(pd_path, nu_path):
            pd_path.unlink()
        else:
            pd_path.rename(pd_path.parent/f"__{pd_path.name}")
            nu_path.rename(nu_path.parent/f"__{nu_path.name}")
    
    elif hd_path.exists() and nu_path.exists():
        if are_equal(hd_path, nu_path):
            hd_path.unlink()
        else:
            hd_path.rename(hd_path.parent/f"__{hd_path.name}")
            nu_path.rename(nu_path.parent/f"__{nu_path.name}")

    elif pd_path.exists():
        pd_path.rename(pd_path.parent/pd_path.name.replace("_PD.","."))
    
    elif hd_path.exists():
        hd_path.rename(hd_path.parent/hd_path.name.replace("_HD.","."))

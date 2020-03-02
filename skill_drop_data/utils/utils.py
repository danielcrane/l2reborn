import os
import numpy as np

util_path = os.path.dirname(os.path.realpath(__file__))
tmp_path = os.path.join(util_path, "..", "tmp")
asm_path = os.path.join(util_path, "l2asm-disasm_1.4.1")
l2encdec_path = os.path.join(util_path, "l2encdec")


def read_encrypted(path, fname):
    """Reads encrypted .dat file
    Note: The input .dat file name must use the original name, otherwise
          it'll fail to find the correct .ddf file for l2asmdism

    Parameters
    ----------
    path : string
        Path of directory containing .dat file
    fname : string
        File name of .dat file

    Returns
    -------
    list
        List containing the lines of the encrypted .dat file

    """
    if fname[-4:] != ".dat":
        raise ValueError("Input to reader must be a .dat file")

    fname_txt = fname.replace(".dat", ".txt")
    fname_ddf = fname.replace(".dat", ".ddf")
    if not os.path.exists(tmp_path):
        # If temporary directory doesn't exist, then make it
        # NOTE: When converted to class based method, this should be in __init__
        os.makedirs(tmp_path)

    os.system(f"{l2encdec_path}/l2encdec.exe -s {path}/{fname} {tmp_path}/dec-{fname}")
    os.system(
        f"{asm_path}/l2disasm -d {asm_path}/DAT_defs/Interlude/{fname_ddf} "
        f"{tmp_path}/dec-{fname} {tmp_path}/{fname_txt}"
    )

    lines = open(f"{tmp_path}/{fname_txt}", "r", encoding="utf8").read().split("\n")
    del lines[-1]

    os.remove(f"{tmp_path}/dec-{fname}")  # Clean up decoded .dat file
    os.remove(f"{tmp_path}/{fname_txt}")  # Clean up readable .txt file
    return lines


def write_encrypted(path, fname, lines):
    """Writes inputted lines to encrypted .dat file
    Note: The input .dat file name must use the original name, otherwise
          it'll fail to find the correct .ddf file for l2asmdism

    Parameters
    ----------
    path : string
        Path to output .dat file to
    fname : string
        File name to output .dat file to
    lines : list
        List of strings containing information to be written

    """
    if fname[-4:] != ".dat":
        raise ValueError("Output of writer must be a .dat file")

    fname_txt = fname.replace(".dat", ".txt")
    fname_ddf = fname.replace(".dat", ".ddf")

    with open(f"{tmp_path}/{fname_txt}", "w", encoding="utf8") as f:
        for line in lines:
            f.write(f"{line}\n")

    os.system(
        f"{asm_path}/l2asm -d {asm_path}/DAT_defs/Interlude/{fname_ddf} "
        f"{tmp_path}/{fname_txt} {tmp_path}/unenc-{fname}"
    )

    os.system(f"{l2encdec_path}/l2encdec.exe -h 413 {tmp_path}/unenc-{fname} {path}/{fname}")
    os.remove(f"{tmp_path}/unenc-{fname}")
    # os.remove(f"{tmp_path}/{fname_txt}")  # Remove readable .txt file


def round_chance(X, n=5):
    """Rounds the fractional probability X as a percentage, rounded to n decimal places
    with trailing zeros removed
    Examples:
        round_chance(0.12345, 2) -> '12.35%'
        round_chance(0.12341, 2) -> '12.34%'

    Parameters
    ----------
    X : float/int
        Probability (between 0 and 1) to be rounded
    n : int
        Number of decimal places to round X to, should be in the range [0, 16] or so

    Returns
    -------
    string
        X represented as a percentage (with % symbol included) with n decimal places

    """

    if X == 1:
        return "100%"
    elif X == 0:
        return "0%"
    elif X > 1:
        raise ValueError("Inputted probability is greater than 1")
    elif X < 0:
        raise ValueError("Inputted probability is less than 0")
    elif n < 0:
        raise ValueError("Number of decimal places n is less than 0")

    X_str = (f"{X:.16f}" + (n + 2) * "0")[2:]  # Convert X to str, pad with zeros, and strip "0."
    # Note that above we convert f to fixed point float to avoid scientific notation (with e-5 etc)
    X_int = int(X_str[:2])  # First two digits of probability become the integer part of percentage
    X_dec = X_str[2 : n + 2]  # The next n digits become the rounded decimal part

    if int(X_str[n + 2]) >= 5:
        # If the end+1 digit is >= 5, must round up
        X_dec = X_dec[:-1] + str(int(X_dec[-1]) + 1)

    X_dec = str(int(X_dec[::-1]))[::-1]  # Remove trailing zeros from decimal portion

    if X_dec == "0" or n == 0:
        X_per = f"{X_int}%"
    else:
        X_per = f"{X_int}.{X_dec}%"

    return X_per

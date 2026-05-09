#!/usr/bin/env python3
"""Estimate payload COM for Franka set_load from measurements in fr3_hand_tcp."""

from math import sqrt

# Edit these centers after measuring from fr3_hand_tcp, in meters.
# Positive/negative directions follow the TF axes shown in RViz.
PARTS = [
    # name, mass_kg, [x_tcp_m, y_tcp_m, z_tcp_m]
    ("realsense_d435i", 0.072, [0.05, -0.1, -0.08]),
    ("charuco_board", 0.095, [0.00, 0.00, 0.15]),
    ("camera_mount", 0.030, [0.025, -0.03, -0.07]),
]

TCP_Z_FROM_LINK8 = 0.1034


def weighted_com(parts):
    total_mass = sum(mass for _, mass, _ in parts)
    com = [
        sum(mass * xyz[i] for _, mass, xyz in parts) / total_mass
        for i in range(3)
    ]
    return total_mass, com


def tcp_to_link8(xyz_tcp):
    x_tcp, y_tcp, z_tcp = xyz_tcp
    root2 = sqrt(2.0)
    return [
        (x_tcp + y_tcp) / root2,
        (-x_tcp + y_tcp) / root2,
        TCP_Z_FROM_LINK8 + z_tcp,
    ]


def main():
    mass, com_tcp = weighted_com(PARTS)
    com_link8 = tcp_to_link8(com_tcp)

    print(f"total_mass_kg = {mass:.6f}")
    print(f"com_in_fr3_hand_tcp_m = [{com_tcp[0]:.6f}, {com_tcp[1]:.6f}, {com_tcp[2]:.6f}]")
    print(f"com_in_fr3_link8_m = [{com_link8[0]:.6f}, {com_link8[1]:.6f}, {com_link8[2]:.6f}]")
    print()
    print(
        "PAYLOAD_MASS={:.6f} PAYLOAD_CX={:.6f} PAYLOAD_CY={:.6f} PAYLOAD_CZ={:.6f} "
        "pixi run payload-set-calib-kit".format(mass, *com_link8)
    )


if __name__ == "__main__":
    main()

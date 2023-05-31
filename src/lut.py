import json
import sys
from typing import NamedTuple
import moderngl
import numpy as np
import time
from PIL import Image
from enum import Enum

LUT_RES = (256, 256)
MAX_CURVATURE = 1.0


class Equation(Enum):
    Dipole = "dipole"
    Gaussian = "gaussian"


class Parameters(NamedTuple):
    sigma_tr: np.ndarray[np.float32]
    albedo: np.ndarray[np.float32]
    zr: np.ndarray[np.float32]
    zv: np.ndarray[np.float32]


def calculate_parameters(sigma_a: np.ndarray[np.float32], sigma_s: np.ndarray[np.float32], g: float, eta: float) -> Parameters:
    sigma_s_prime = sigma_s * (1.0 - g)
    sigma_t_prime = sigma_s_prime + sigma_a
    alpha_prime = sigma_s_prime / sigma_t_prime
    fresnel = -1.440 / eta / eta + 0.710 / eta + 0.668 + 0.0636 * eta
    a = (1.0 + fresnel) / (1.0 - fresnel)
    albedo = 0.5 * alpha_prime * (1.0 + np.exp(-4.0 / 3.0 * a * np.sqrt(3.0 * (1.0 - alpha_prime)))) / (
                1.0 + np.sqrt(3.0 * (1.0 - alpha_prime)))
    sigma_tr = np.sqrt(3.0 * (1.0 - alpha_prime)) * sigma_t_prime
    zr = 1.0 / sigma_t_prime
    zv = (1.0 + 4.0 / 3.0 * a) / sigma_t_prime
    return Parameters(sigma_tr, albedo, zr, zv)


def generate_lut():
    print("Generating Look-up-table for Penner SSS...")
    start = time.time()
    ctx = moderngl.create_standalone_context()
    filename = sys.argv[1]
    with open(filename, "r") as file:
        scene = json.load(file)
    if scene["equation"].lower() == "dipole":
        equation = Equation.Dipole
    elif scene["equation"].lower() == "gaussian":
        equation = Equation.Gaussian
    else:
        print(f"Unknown diffusion profile type")
        exit(1)
    sigma_a = np.array(scene["sigma_a"], dtype=np.float32)
    sigma_s = np.array(scene["sigma_s"], dtype=np.float32)
    g, eta = scene["g"], scene["eta"]
    global MAX_CURVATURE
    MAX_CURVATURE = scene["max-curvature"]
    parameters = calculate_parameters(sigma_a, sigma_s, g, eta)
    quad = ctx.buffer(
        np.hstack([
            np.array([[-1, -1], [1, -1], [1, 1], [-1, -1], [1, 1], [-1, 1]], dtype=np.float32),
            np.zeros((6, 1), dtype=np.float32)
        ])
    )
    with open("shaders/pass-0.glsl", "r") as f:
        shader_source = f.read()
    program = ctx.program(
        vertex_shader=shader_source.replace("SHADER_TYPE", "VERTEX_SHADER"),
        fragment_shader=shader_source.replace("SHADER_TYPE", "FRAGMENT_SHADER").replace("DIFFUSION_PROFILE", "GAUSSIAN" if equation == Equation.Gaussian else "DIPOLE")
    )
    if equation == Equation.Dipole:
        program["zr"].write(parameters.zr)
        program["zv"].write(parameters.zv)
        program["sigmaTr"].write(parameters.sigma_tr)
    program["albedo"].write(parameters.albedo)
    program["maxCurvature"] = MAX_CURVATURE
    vao = ctx.vertex_array(program, quad, "vertPos")
    lut_texture = ctx.texture(LUT_RES, 3, dtype="f1")
    framebuffer = ctx.framebuffer([lut_texture])
    with ctx.scope(framebuffer):
        framebuffer.clear()
        vao.render()
    buffer = bytearray(LUT_RES[0] * LUT_RES[1] * 3)
    lut_texture.read_into(buffer)
    Image.frombuffer("RGB", LUT_RES, bytes(buffer)).save("look_up_table.png")
    print("LUT generation done...")
    print(f"LUT generation took {time.time() - start} seconds.")

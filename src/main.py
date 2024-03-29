import json
import struct
import sys

import moderngl
import numba
import numpy as np
import tinyobjloader
from OpenGL import GL as gl
from PIL import Image
from matplotlib import pyplot as plt
from pyrr import Vector3
from camera import Camera
from lut import generate_lut, LUT_RES


@numba.jit
def normal_array_kernel(triangle_array, normal_index_array, normal_vectors, vertex_num):
    normal_array = np.empty((vertex_num, 3), dtype=np.float32)
    for normal_index, vertex_index in zip(normal_index_array, triangle_array):
        normal_array[vertex_index] = normal_vectors[normal_index]
    return normal_array


@numba.jit
def ccw_check_kernel(triangle_array, vertex_array, normal_array):
    for i in range(0, len(triangle_array), 3):
        i0, i1, i2 = triangle_array[i:i + 3]
        p0, p1, p2 = vertex_array[i0], vertex_array[i1], vertex_array[i2]
        n = np.cross(p1 - p0, p2 - p0)
        if np.dot(n, normal_array[i0]) < 0:
            triangle_array[i], triangle_array[i + 1] = i1, i0


def main():
    res = (1024, 1024)
    if len(sys.argv) < 2:
        print("Usage: python ./src/main.py ./scene/<scene-to-render.json>")
        exit(1)
    generate_lut()
    filename = sys.argv[1]
    with open(filename, "r") as file:
        scene = json.load(file)
    reader = tinyobjloader.ObjReader()
    if not reader.ParseFromFile(scene["render_model"]):
        print("Failed to parse model")
        exit(0)
    else:
        print("Received model data...")
    attrib = reader.GetAttrib()
    vertex_array = np.array(attrib.vertices, dtype=np.float32).reshape(-1, 3)
    normal_vectors = np.array(attrib.normals, dtype=np.float32).reshape(-1, 3)
    normal_index_array = np.array([
        index.normal_index for shape in reader.GetShapes() for index in shape.mesh.indices
    ], dtype=np.int32)
    triangle_array = np.array([
        index.vertex_index for shape in reader.GetShapes() for index in shape.mesh.indices
    ], dtype=np.int32)
    normal_array = normal_array_kernel(triangle_array, normal_index_array, normal_vectors, vertex_array.shape[0])
    normal_array /= np.linalg.norm(normal_array, axis=1).reshape((-1, 1))
    ccw_check_kernel(triangle_array, vertex_array, normal_array)
    print("Model data parsing done...")
    ctx = moderngl.create_standalone_context(330)
    ibo = ctx.buffer(triangle_array)
    nbo = ctx.buffer(normal_array)
    vbo = ctx.buffer(vertex_array)
    with open("shaders/vertex.glsl", "r") as f:
        vertex_shader_source = f.read()
    with open("shaders/fragment.glsl", "r") as f:
        fragment_shader_source = f.read()
    program = ctx.program(
        vertex_shader=vertex_shader_source,
        fragment_shader=fragment_shader_source
    )
    camera = Camera(Vector3([0.0, 1.0, -10.0]), Vector3([0.0, 0.5, 0.0]), res, 20.0)
    program["mvp"].write(camera.mvp)
    vao = ctx.vertex_array(
        program,
        [
            (vbo, "3f", "vertex_pos"),
            (nbo, "3f", "vertex_normal")
        ],
        index_buffer=ibo
    )
    depth_buffer = ctx.depth_renderbuffer(res, samples=4)
    point_light_size = struct.calcsize("=3f4x3f4x")
    point_light_array = scene["point_lights"]
    buffer = bytearray(max(len(point_light_array), 1) * point_light_size)
    view = memoryview(buffer)
    for i, point_light in enumerate(point_light_array):
        view[i * point_light_size:(i + 1) * point_light_size] = struct.pack(
            "=3f4x3f4x",
            *point_light["emission"],
            *point_light["position"]
        )
    point_light_buffer = ctx.buffer(buffer)
    direction_light_size = struct.calcsize("=3f4x3f4x")
    direction_light_array = scene["direction_lights"]
    buffer = bytearray(max(len(direction_light_array), 1) * direction_light_size)
    view = memoryview(buffer)
    for i, direction_light in enumerate(direction_light_array):
        view[i * direction_light_size:(i + 1) * direction_light_size] = struct.pack(
            "=3f4x3f4x",
            *direction_light["emission"],
            *direction_light["direction"]
        )
    direction_light_buffer = ctx.buffer(buffer)
    look_up_table = ctx.texture(LUT_RES, 3, Image.open("look_up_table.png").tobytes(), dtype="f1")
    look_up_table.repeat_x = False
    look_up_table.repeat_y = False
    program["lut"] = 0
    look_up_table.use(0)
    program["min_curvature"] = scene["min-curvature"]
    program["max_curvature"] = scene["max-curvature"]
    program["num_point_lights"] = len(point_light_array)
    program["num_direction_lights"] = len(direction_light_array)
    point_light_buffer.bind_to_uniform_block(0)
    direction_light_buffer.bind_to_uniform_block(1)
    render_target_msaa = ctx.texture(res, 3, samples=4, dtype='f4')
    render_target = ctx.texture(res, 3, dtype="f4")
    framebuffer_msaa = ctx.framebuffer([render_target_msaa], depth_attachment=depth_buffer)
    framebuffer = ctx.framebuffer([render_target])
    with ctx.scope(framebuffer_msaa, moderngl.DEPTH_TEST | moderngl.CULL_FACE):
        framebuffer_msaa.clear()
        vao.render()
    gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, framebuffer_msaa.glo)
    gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, framebuffer.glo)
    gl.glBlitFramebuffer(0, 0, res[0], res[1], 0, 0, res[0], res[1], gl.GL_COLOR_BUFFER_BIT, gl.GL_LINEAR)
    canvas_buffer = bytearray(res[0] * res[1] * 4 * 3)
    render_target.read_into(canvas_buffer)
    postfix = sys.argv[1].split('/')[-1].split('\\')[-1].split('.')[0] + '-' + scene["equation"].lower().split('.')[-1]
    plt.imsave(f"result-{postfix}.png", np.frombuffer(canvas_buffer, dtype=np.float32).reshape(res + (-1,))[::-1, ::-1])


if __name__ == "__main__":
    main()

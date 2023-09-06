#version 330
in vec3 vertex_pos;
in vec3 vertex_normal;
out vec3 fragment_pos;
out vec3 fragment_normal;
uniform mat4 mvp;
void main()
{
    gl_Position = mvp * vec4(vertex_pos, 1.0);
    fragment_pos = vertex_pos;
    fragment_normal = vertex_normal;
}
